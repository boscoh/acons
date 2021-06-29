
# ACONS

An asynchronous command-line runner for use in async web-servers like [fastapi](https://fastapi.tiangolo.com/).

Sometimes, you want to run command-line utilities and expose the output to a web-server. However, it's a bit tricky to capture the console output while it's running, and also allow the web-client to kill the job mid-process.

`acons` can execute command-line processes as an async function, where output can be retrieved via another async function, and a kill signal can be sent at any time.

### Install

    pip install acons

### run

Function interface:

    run(command, run_dir=None, is_parse=False, job_id=None)

 - `command`: str of command-line command
 - `run_dir`: optional starting directory of the command
 - `is_parse`: optional flag to parse the output as tsv file into a list
             of dictionaries
 - `job_id`: optional id that will be used to `flush_lines` and `kill_job`

To use in an async function:

    await acons.run('ls', job_id='my-special-id-123')

To test the output in a sync version:

    import acons
    output = acons.sync_run('ls')
    
### flush_lines

In an async function:
    
    lines = await acons.flush_lines('my-special-id-123')

This will return the console lines produced by the job since the last call to `acons.flush_lines`

### kill_job

In an async function:

    `await kill_job('my-special-id-123')

Sends the kill signal for the job.

### Parameters d

`acons.RUN_INTERVAL_IN_S = 0.2` - determines how long the function polls for each interval

`acons.SLEEP_INTERVAL_IN_S = 0.5` - determines how long the function sleeps between intervals

`acons.N_MAX_JOB = 100` - maximum number of jobs that stores output using an LRU cache

## Example server

A simple fastapi-server/vue-client is included that demonstrates `acons` in action. 

Concurrent command-line commands can be typed in and executed. The console output will be piped back into the web-client, and the job can be cancelled at any time.

When the job is completed, the entire console output is made available through the Monaco web-editor . 

Download the .zip version of this package, then run the server:

    ./test-server.sh

which is essentially:

    uvicorn server:app --reload --port=5200

Communication between client/server is via an rpc-json interface as described in [rpcseed](https://github.com/boscoh/rpcseed).

