# cython: language_level=3
# cython: boundscheck=False
# cython: wraparound=False
# distutils: language = c++
# distutils: extra_compile_args = -std=c++11
from libcpp.atomic cimport atomic
cdef extern from "unistd.h":
    int dup(int oldfd)
    int dup2(int oldfd, int newfd)
    int close(int fd)
cdef extern from "stdio.h":
    ctypedef struct FILE:
        pass
    FILE *stdout
    int fflush(FILE *stream)
    FILE* fdopen(int fd, const char *mode)
    int fclose(FILE *stream)
    int printf(const char *format, ...) noexcept nogil

cdef atomic[int] g_level
g_level.store(LoggerLevel.NOT_SET)

cdef void set_logger_level(LoggerLevel level) noexcept nogil:
    g_level.store(level)

cdef int can_log(LoggerLevel level) noexcept nogil:
    if level >= g_level.load():
        return 1
    return 0

cdef int no_log(const char* format, ...) noexcept nogil:
    pass

cdef log_f log_error() noexcept nogil:
    if 1 == can_log(LoggerLevel.ERROR):
        return printf
    return no_log

cdef log_f log_warning() noexcept nogil:
    if 1 == can_log(LoggerLevel.WARNING):
        return printf
    return no_log

cdef log_f log_info() noexcept nogil:
    if 1 == can_log(LoggerLevel.INFO):
        return printf
    return no_log

cdef log_f log_debug() noexcept nogil:
    if 1 == can_log(LoggerLevel.DEBUG):
        return printf
    return no_log

cdef py_set_logger_level(int level):
    cdef LoggerLevel elevel
    if level == LoggerLevel.ERROR:
        elevel = LoggerLevel.ERROR
    elif level == LoggerLevel.WARNING:
        elevel = LoggerLevel.WARNING
    elif level == LoggerLevel.INFO:
        elevel = LoggerLevel.INFO
    elif level == LoggerLevel.DEBUG:
        elevel = LoggerLevel.DEBUG
    else:
        elevel = LoggerLevel.NOT_SET
    set_logger_level(elevel)

cdef int py_set_new_sys_stdout(int new_stdout_fd):
    cdef int original_fd = dup(1)
    # cdef FILE* newstdOut = fdopen(new_stdout_fd, "w+")
    fflush(stdout)
    dup2(new_stdout_fd, 1)
    return original_fd

cdef py_set_original_sys_stdout(int original_stdout_fd):
    fflush(stdout)
    close(dup2(original_stdout_fd, 1))

