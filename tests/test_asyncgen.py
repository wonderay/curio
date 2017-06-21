# test_asyncgen.py

import pytest
from curio import *
from curio.meta import finalize, awaitable, safe_generator, AsyncABC, abstractmethod


# Test to make sure a simple async generator runs
def test_simple_agen(kernel):
    async def countdown(n):
        while n > 0:
            yield n
            n -= 1

    async def main():
        nums = [ n async for n in countdown(5) ]
        assert nums == [5, 4, 3, 2, 1]

    kernel.run(main())

# Test to make sure a simple finally clause executes
def test_simple_agen_final(kernel):
    results = []
    async def countdown(n):
        try:
            while n > 0:
                yield n
                n -= 1
        finally:
            results.append('done')

    async def main():
        nums = [ n async for n in countdown(5) ]
        assert nums == [5, 4, 3, 2, 1]

    kernel.run(main())
    assert results == ['done']

# Test to make sure finally clause with async fails
def test_agen_final_fail(kernel):
    async def countdown(n):
        try:
            while n > 0:
                yield n
                n -= 1
        finally:
            await sleep(0.0)

    async def main():
        with pytest.raises(RuntimeError):
            nums = [n async for n in countdown(5) ]

    kernel.run(main())

# Make sure async-with in finally causes failure
def test_agen_final_fail_with(kernel):
    async def countdown(n):
        try:
            while n > 0:
                yield n
                n -= 1
        finally:
            async with something:
                pass

    async def main():
        with pytest.raises(RuntimeError):
            nums = [n async for n in countdown(5) ]

    kernel.run(main())

# Make sure async-for in finally causes failure
def test_agen_final_fail_iter(kernel):
    async def countdown(n):
        try:
            while n > 0:
                yield n
                n -= 1
        finally:
            async for x in something:
                pass

    async def main():
        with pytest.raises(RuntimeError):
            nums = [n async for n in countdown(5) ]

    kernel.run(main())

# Make sure application of finalize() works
def test_agen_final_finalize(kernel):
    async def countdown(n):
        try:
            while n > 0:
                yield n
                n -= 1
        finally:
            await sleep(0.0)

    async def main():
        async with finalize(countdown(5)) as c:
            nums = [n async for n in c]
            assert nums == [5, 4, 3, 2, 1]

    kernel.run(main())

# Make sure async-with statement causes failure
def test_agen_with_fail(kernel):
    lck = Lock()

    async def countdown(n):
        async with lck:
            while n > 0:
                yield n
                n -= 1

    async def main():
        with pytest.raises(RuntimeError):
            nums = [n async for n in countdown(5) ]

    kernel.run(main())

# Make sure async in try-except causes failure
def test_agen_except_fail(kernel):
    async def countdown(n):
        while n > 0:
             try:
                 yield n
             except Exception:
                 await sleep(0.0)
             n -= 1

    async def main():
        with pytest.raises(RuntimeError):
            nums = [n async for n in countdown(5) ]

    kernel.run(main())

# Make sure a try-except without asyncs works
def test_agen_except_ok(kernel):
    async def countdown(n):
        while n > 0:
             try:
                 yield n
             except Exception:
                 pass
             n -= 1

    async def main():
        nums = [n async for n in countdown(5) ]
        assert nums == [5, 4, 3, 2, 1]

    kernel.run(main())

# Test to make sure a simple async generator runs
def test_awaitable_agen(kernel):
    async def countdown(n):
        while n > 0:
             try:
                 yield n
             except Exception:
                 pass
             n -= 1

    def add(x, y):
        return x + y

    @awaitable(add)
    async def add(x, y):
        return x + y

    async def main():
        nums = [ await add(n,n) async for n in countdown(5) ]
        assert nums == [10, 8, 6, 4, 2]

    kernel.run(main())

    nums = [ add(n,n) for n in range(5,0,-1) ]
    assert nums == [10, 8, 6, 4, 2]

def test_agen_safe_override(kernel):
    @safe_generator
    async def countdown(n):
        try:
            while n > 0:
                yield n
                n -= 1
        finally:
            await sleep(0.0)

    async def main():
        nums = [n async for n in countdown(5) ]
        assert nums == [5, 4, 3, 2, 1]

    kernel.run(main())

def test_asyncapc_generator_function():
    class Parent(AsyncABC):
        @abstractmethod
        async def foo(self):
            raise NotImplementedError

    class Child(Parent):
        async def foo(self):
            yield 1
            return
