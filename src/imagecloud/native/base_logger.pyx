# cython: language_level=3
# cython: boundscheck=False
# cython: wraparound=False
# distutils: language = c++
# distutils: extra_compile_args = -std=c++11
cdef extern from "stdarg.h":
    ctypedef struct __va_list_tag:
        pass
    ctypedef __va_list_tag* va_list
    void va_start(va_list ap, ...) noexcept nogil
    void va_end(va_list ap) noexcept nogil
    int vsnprintf(char *str, unsigned int size, const char *format, va_list ap) noexcept nogil
cdef BaseLogger g_logger
cdef object g_py_log
cdef char* format_var_args(LoggerLevel level, const char* format_str, va_list args) noexcept nogil:
    cdef char fbuf[512]
    cdef int size = vsnprintf(NULL, 0, format_str, args) + 1
    vsnprintf(fbuf, size, format_str, args)
    return fbuf

cdef void log_py(LoggerLevel level, str msg):
    global g_py_log
    if g_py_log is None:
        print('{0:X} | {1}'.format(level, msg))
    else:
        g_py_log(level, msg)


cdef py_callback_log(LoggerLevel level, char* message):
    cdef str msg = message.decode('utf-8','replace')
    log_py(level, msg)

cdef void set_logger(int level, object callback) noexcept nogil:
    global g_logger
    global g_py_log
    if level == LoggerLevel.ERROR:
        g_logger.level = LoggerLevel.ERROR
    elif level == LoggerLevel.WARNING:
        g_logger.level = LoggerLevel.WARNING
    elif level == LoggerLevel.INFO:
        g_logger.level = LoggerLevel.INFO
    elif level == LoggerLevel.DEBUG:
        g_logger.level = LoggerLevel.DEBUG
    else:
        g_logger.level = LoggerLevel.NOT_SET
    with gil:
        g_py_log = callback

cdef void log_error(const char* format, ...) noexcept nogil:
    global g_logger
    cdef va_list args
    cdef char* result
    if LoggerLevel.ERROR < g_logger.level:
        return
    va_start(args, format)
    result = format_var_args(LoggerLevel.ERROR, format, args)
    va_end(args)
    if result != NULL:
        with gil:
            py_callback_log(LoggerLevel.ERROR, result)


cdef void log_warning(const char* format, ...) noexcept nogil:
    global g_logger
    cdef va_list args
    cdef char* result
    if LoggerLevel.WARNING < g_logger.level:
        return
    va_start(args, format)
    result = format_var_args(LoggerLevel.WARNING, format, args)
    va_end(args)
    if result != NULL:
        with gil:
            py_callback_log(LoggerLevel.WARNING, result)

cdef void log_info(const char* format, ...) noexcept nogil:
    global g_logger
    cdef va_list args
    cdef char* result
    if LoggerLevel.INFO < g_logger.level:
        return
    va_start(args, format)
    result = format_var_args(LoggerLevel.INFO, format, args)
    va_end(args)
    if result != NULL:
        with gil:
            py_callback_log(LoggerLevel.INFO, result)

cdef void log_debug(const char* format, ...) noexcept nogil:
    global g_logger
    cdef va_list args
    cdef char* result
    if LoggerLevel.DEBUG < g_logger.level:
        return
    va_start(args, format)
    result = format_var_args(LoggerLevel.DEBUG, format, args)
    va_end(args)
    if result != NULL:
        with gil:
            py_callback_log(LoggerLevel.DEBUG, result)

def native_set_base_logger(
    level: int, 
    callback: Callable[[int, str], None] | None = None
): # return nothing
    set_logger(level, callback)