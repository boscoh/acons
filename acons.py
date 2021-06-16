import asyncio
import fcntl
import logging
import os
import re
import subprocess
import time

import pylru

__doc__ = """
Asynchronous command-line process management
"""

logger = logging.getLogger(__name__)

run_interval_in_s = 0.2
sleep_interval_in_s = 0.5
n_max_job = 100

output_lines_by_job_id = pylru.lrucache(n_max_job)
terminate_by_job_id = pylru.lrucache(n_max_job)

lock = asyncio.Lock()


async def flush_console_lines(job_id):
    """
    Pops off the latest output lines associated with job_id
    """
    async with lock:
        if job_id not in output_lines_by_job_id:
            result = []
        else:
            result = output_lines_by_job_id[job_id]
            output_lines_by_job_id[job_id] = []
    return result


def escape_ansi(line):
    ansi_escape = re.compile(r"(?:\x1B[@-_]|[\x80-\x9F])[0-?]*[ -/]*[@-~]")
    return ansi_escape.sub("", line)


def parse_output_table(txt):
    """
    Returns list of dictionary values that maps tsv output with a header row
    """
    lines = txt.splitlines()

    header = lines[0].lower()
    tokens = [h.replace(" ", "_") for h in header.split()]

    parse_list = []
    for token in tokens:
        i_token = header.index(token)
        parse_list.append(dict(token=token, i=i_token))
    for i in range(len(tokens) - 1):
        parse_list[i]["j"] = parse_list[i + 1]["i"]
    parse_list[-1]["j"] = len(header) + 100

    rows = []
    for line in lines[1:]:
        row = {}
        for parse in parse_list:
            val = line[parse["i"] : parse["j"]]
            row[parse["token"]] = val.strip()
        rows.append(row)

    return rows


async def kill_job(job_id):
    """Set kill signal for job"""
    async with lock:
        terminate_by_job_id[job_id] = True


def set_non_blocking(fd):
    """
    Set the file description of the given file descriptor to non-blocking.
    https://stackoverflow.com/a/19893052
    """
    flags = fcntl.fcntl(fd, fcntl.F_GETFL)
    flags = flags | os.O_NONBLOCK
    fcntl.fcntl(fd, fcntl.F_SETFL, flags)


async def os_run(command, run_dir=None, is_parse=False, job_id=None):
    """
    Runs a system command and saves the console output in
    a globally accessible cache that is accessible
    asynchronously from `flush_console_lines`.

    :param command: terminal command
    :param run_dir: directory to run the command in
    :param is_parse: parse with tsv output into dictionary
    :type arg: bool
    :param job_id: id to allow async fetching of console and async termination

    :returns: { "exitCode": int, "output": <str|list<str>> }
    """
    logger.info(f"os_run '{command}' in '{run_dir}' with id='{job_id}'")

    if run_dir:
        os.chdir(run_dir)

    if job_id:
        async with lock:
            output_lines_by_job_id[job_id] = []
            terminate_by_job_id[job_id] = False

    process = subprocess.Popen(
        command,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    # avoid interactive processes blocking the server
    set_non_blocking(process.stdout)

    lines = []

    async def push_lines_to_output_cache():
        if not lines:
            return
        if job_id:
            async with lock:
                output_lines_by_job_id[job_id].extend(lines)
        for line in lines:
            logger.debug(f"os_run(id={job_id})>>  {line}")
        lines.clear()

    output = ""
    tick = time.time()

    while True:
        txt = process.stdout.readline().decode("utf-8", errors="ignore")
        txt = escape_ansi(txt)

        output += txt
        lines.extend(txt.splitlines())

        # check for kill signal
        if terminate_by_job_id.get(job_id):
            logger.info(f"os_run terminate '{job_id}'")
            process.terminate()
            break

        if txt == "" and process.poll() is not None:
            break

        # allow other tasks to run
        if time.time() - tick > run_interval_in_s:
            await push_lines_to_output_cache()
            await asyncio.sleep(sleep_interval_in_s)
            tick = time.time()

    await push_lines_to_output_cache()

    exec_code = process.returncode
    if exec_code == 0:
        output = str(output)
        if is_parse:
            output = parse_output_table(output)
        return {"exitCode": exec_code, "output": output}
    else:
        return {"exitCode": exec_code, "output": output}


def get_output(command, run_dir=None, is_parse=False):
    """Synchronous version of os_run"""
    return asyncio.run(os_run(command, run_dir, is_parse))
