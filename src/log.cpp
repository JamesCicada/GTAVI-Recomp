#include "gtavi/log.h"

#include <cstdio>
#include <ctime>
#include <utility>

namespace gtavi {
namespace {

constexpr char to_lower_ascii(char c) noexcept {
    return (c >= 'A' && c <= 'Z') ? static_cast<char>(c - 'A' + 'a') : c;
}

bool equals_ignore_case(std::string_view lhs, std::string_view rhs) noexcept {
    if (lhs.size() != rhs.size()) {
        return false;
    }
    for (std::size_t i = 0; i < lhs.size(); ++i) {
        if (to_lower_ascii(lhs[i]) != to_lower_ascii(rhs[i])) {
            return false;
        }
    }
    return true;
}

}  // namespace

std::string_view to_string(LogLevel level) noexcept {
    switch (level) {
        case LogLevel::Trace:
            return "trace";
        case LogLevel::Debug:
            return "debug";
        case LogLevel::Info:
            return "info";
        case LogLevel::Warn:
            return "warn";
        case LogLevel::Error:
            return "error";
        case LogLevel::Critical:
            return "critical";
    }
    return "unknown";
}

LogLevel log_level_from_string(std::string_view text, LogLevel fallback) noexcept {
    if (equals_ignore_case(text, "trace")) {
        return LogLevel::Trace;
    }
    if (equals_ignore_case(text, "debug")) {
        return LogLevel::Debug;
    }
    if (equals_ignore_case(text, "info")) {
        return LogLevel::Info;
    }
    if (equals_ignore_case(text, "warn") || equals_ignore_case(text, "warning")) {
        return LogLevel::Warn;
    }
    if (equals_ignore_case(text, "error")) {
        return LogLevel::Error;
    }
    if (equals_ignore_case(text, "critical")) {
        return LogLevel::Critical;
    }
    return fallback;
}

void Logger::set_level(LogLevel level) {
    const std::lock_guard<std::mutex> lock(mutex_);
    level_ = level;
}

LogLevel Logger::level() const {
    const std::lock_guard<std::mutex> lock(mutex_);
    return level_;
}

bool Logger::should_log(LogLevel level) const {
    const std::lock_guard<std::mutex> lock(mutex_);
    return static_cast<int>(level) >= static_cast<int>(level_);
}

void Logger::add_sink(LogSink sink) {
    const std::lock_guard<std::mutex> lock(mutex_);
    sinks_.push_back(std::move(sink));
}

void Logger::clear_sinks() {
    const std::lock_guard<std::mutex> lock(mutex_);
    sinks_.clear();
}

void Logger::log(LogLevel level, std::string_view message) {
    // Copy the sink list so that no lock is held while a sink runs. This lets a
    // sink log through a different Logger without deadlocking.
    std::vector<LogSink> sinks;
    {
        const std::lock_guard<std::mutex> lock(mutex_);
        if (static_cast<int>(level) < static_cast<int>(level_)) {
            return;
        }
        sinks = sinks_;
    }

    if (sinks.empty()) {
        return;
    }

    const LogRecord record{std::chrono::system_clock::now(), level, message};
    for (const auto& sink : sinks) {
        sink(record);
    }
}

Logger& Logger::default_logger() {
    static Logger logger;
    return logger;
}

std::string format_timestamp_iso8601(std::chrono::system_clock::time_point time) {
    const std::time_t seconds = std::chrono::system_clock::to_time_t(time);
    std::tm broken_down{};
#if defined(_WIN32)
    if (gmtime_s(&broken_down, &seconds) != 0) {
        return "invalid-time";
    }
#else
    if (gmtime_r(&seconds, &broken_down) == nullptr) {
        return "invalid-time";
    }
#endif

    char buffer[32]{};
    const int written = std::snprintf(buffer, sizeof(buffer), "%04d-%02d-%02dT%02d:%02d:%02dZ",
                                      broken_down.tm_year + 1900, broken_down.tm_mon + 1,
                                      broken_down.tm_mday, broken_down.tm_hour, broken_down.tm_min,
                                      broken_down.tm_sec);
    if (written < 0) {
        return "invalid-time";
    }
    return std::string{buffer};
}

LogSink make_stderr_sink() {
    return [](const LogRecord& record) {
        const std::string timestamp = format_timestamp_iso8601(record.time);
        const std::string_view level = to_string(record.level);
        std::fprintf(stderr, "[%s] [%.*s] %.*s\n", timestamp.c_str(), static_cast<int>(level.size()),
                     level.data(), static_cast<int>(record.message.size()), record.message.data());
        std::fflush(stderr);
    };
}

LogSink make_stream_sink(std::ostream& stream) {
    return [&stream](const LogRecord& record) {
        stream << '[' << format_timestamp_iso8601(record.time) << "] [" << to_string(record.level)
               << "] " << record.message << '\n';
    };
}

}  // namespace gtavi
