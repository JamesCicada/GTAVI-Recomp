#include "gtavi/log.h"

#include <sstream>
#include <string>
#include <vector>

#include "test_framework.h"

using gtavi::LogLevel;
using gtavi::Logger;
using gtavi::LogRecord;

GTAVI_TEST(logger_drops_records_below_level) {
    Logger logger;
    logger.set_level(LogLevel::Info);

    std::vector<std::string> captured;
    logger.add_sink([&captured](const LogRecord& record) { captured.emplace_back(record.message); });

    logger.debug("hidden");
    logger.info("shown");

    CHECK_EQ(captured.size(), std::size_t{1});
    CHECK_EQ(captured.front(), std::string{"shown"});
}

GTAVI_TEST(logger_delivers_to_every_sink_in_order) {
    Logger logger;
    std::vector<std::string> first;
    std::vector<std::string> second;
    logger.add_sink([&first](const LogRecord& record) { first.emplace_back(record.message); });
    logger.add_sink([&second](const LogRecord& record) { second.emplace_back(record.message); });

    logger.warn("payload");

    CHECK_EQ(first.size(), std::size_t{1});
    CHECK_EQ(second.size(), std::size_t{1});
    CHECK_EQ(first.front(), std::string{"payload"});
}

GTAVI_TEST(logger_clear_sinks_stops_delivery) {
    Logger logger;
    int calls = 0;
    logger.add_sink([&calls](const LogRecord&) { ++calls; });
    logger.info("first");
    logger.clear_sinks();
    logger.info("second");

    CHECK_EQ(calls, 1);
}

GTAVI_TEST(logger_reports_level_on_record) {
    Logger logger;
    LogLevel observed = LogLevel::Trace;
    logger.add_sink([&observed](const LogRecord& record) { observed = record.level; });
    logger.error("boom");

    CHECK_TRUE(observed == LogLevel::Error);
}

GTAVI_TEST(logger_should_log_matches_level) {
    Logger logger;
    logger.set_level(LogLevel::Warn);
    CHECK_FALSE(logger.should_log(LogLevel::Info));
    CHECK_TRUE(logger.should_log(LogLevel::Warn));
    CHECK_TRUE(logger.should_log(LogLevel::Critical));
    CHECK_TRUE(logger.level() == LogLevel::Warn);
}

GTAVI_TEST(default_logger_is_a_singleton) {
    CHECK_TRUE(&Logger::default_logger() == &Logger::default_logger());
}

GTAVI_TEST(sink_may_log_to_another_logger) {
    Logger outer;
    Logger inner;
    int inner_calls = 0;

    inner.add_sink([&inner_calls](const LogRecord&) { ++inner_calls; });
    outer.add_sink([&inner](const LogRecord& record) { inner.info(record.message); });

    outer.info("forwarded");

    CHECK_EQ(inner_calls, 1);
}

GTAVI_TEST(log_level_names_round_trip) {
    CHECK_TRUE(gtavi::log_level_from_string("trace", LogLevel::Info) == LogLevel::Trace);
    CHECK_TRUE(gtavi::log_level_from_string("DEBUG", LogLevel::Info) == LogLevel::Debug);
    CHECK_TRUE(gtavi::log_level_from_string("info", LogLevel::Trace) == LogLevel::Info);
    CHECK_TRUE(gtavi::log_level_from_string("warning", LogLevel::Trace) == LogLevel::Warn);
    CHECK_TRUE(gtavi::log_level_from_string("error", LogLevel::Trace) == LogLevel::Error);
    CHECK_TRUE(gtavi::log_level_from_string("Critical", LogLevel::Trace) == LogLevel::Critical);
    CHECK_TRUE(gtavi::log_level_from_string("nonsense", LogLevel::Warn) == LogLevel::Warn);
}

GTAVI_TEST(level_names_are_lowercase) {
    CHECK_EQ(gtavi::to_string(LogLevel::Warn), std::string{"warn"});
    CHECK_EQ(gtavi::to_string(LogLevel::Critical), std::string{"critical"});
}

GTAVI_TEST(timestamp_is_iso8601_utc) {
    const auto time = std::chrono::system_clock::from_time_t(0);
    CHECK_EQ(gtavi::format_timestamp_iso8601(time), std::string{"1970-01-01T00:00:00Z"});
}

GTAVI_TEST(stream_sink_writes_one_line_per_record) {
    Logger logger;
    std::ostringstream stream;
    logger.add_sink(gtavi::make_stream_sink(stream));

    logger.info("hello");

    const std::string output = stream.str();
    CHECK_TRUE(output.find("hello") != std::string::npos);
    CHECK_TRUE(output.find("[info]") != std::string::npos);
    CHECK_EQ(output.back(), '\n');
}
