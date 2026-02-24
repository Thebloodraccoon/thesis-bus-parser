"""Centralized exceptions to the application."""


class ScraperException(Exception):
    """The basic exception for all scrub mistakes."""

    pass


class ParserException(ScraperException):
    """An exception for parser errors."""

    pass


class ParserTimeoutException(ParserException):
    """An exception for the Parser timeouts."""

    pass


class ParserConnectionException(ParserException):
    """An exception for errors of connecting parsers."""

    pass


class ElasticsearchException(ScraperException):
    """Exception for Elasticsearch errors."""

    pass
