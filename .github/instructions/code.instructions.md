---
applyTo: '**'
---

# Experiments & tools

This document provides guidance for understanding and developing tools in this repository


### Setting up a project

If the project is a Python script always start with:
- Create a .gitignore file
- Create a requirements.txt file
- create a minimal build.bat script that 
   - creates a virtual environment if not present
   - activate the enviroment
   - install the requirements.txt
- Create a minimal Readme.md
   - with description
   - how to activate the enviroment
   - how to build (build.bat)    
- Ask if the user wants to have a debugging profile

### Writing code for a project
- When writing small tools try to keep the following structure:
   \<libname>\<libfiles>
   \cli\<cli_app_name>
   \test\<test_tools>
   
- when running the code, make sure the enviroment is activated
- if a library is needed install it in the requirements, then install the project via the requirements file
- When code is done, ask if it needs to be debugged.
- When testing code, if is more than a single line test, make it into a python file in \test\



## Async Programming Patterns

When creating asynchronous tools, use `anyio` for structured concurrency. Here are the key patterns:

### Basic Async Operations

```python
import anyio

async def my_async_function():
    # Sleep without blocking
    await anyio.sleep(1.0)
    
    # Perform async I/O
    result = await some_async_operation()
    return result
```

### Task Groups for Concurrent Operations

```python
async def run_concurrent_tasks():
    async with anyio.create_task_group() as tg:
        tg.start_soon(task1)
        tg.start_soon(task2)
        tg.start_soon(task3)
    # All tasks complete before continuing
```

### Event Synchronization

```python
class MyModule:
    def __init__(self):
        self.connected = anyio.Event()
        
    async def wait_for_connection(self):
        await self.connected.wait()
        
    def on_connected(self):
        self.connected.set()
```

### Cancellation Handling

```python
async def cancellable_operation():
    try:
        while True:
            await anyio.sleep(1)
            # Do work
    except anyio.get_cancelled_exc_class():
        # Cleanup on cancellation
        await cleanup()
        raise
```

### Background Tasks

```python
class ServiceModule:
    async def start_background_service(self):
        async with anyio.create_task_group() as tg:
            tg.start_soon(self._background_worker)
            
    async def _background_worker(self):
        while True:
            try:
                await self._do_work()
                await anyio.sleep(0.1)
            except anyio.get_cancelled_exc_class():
                break
```


