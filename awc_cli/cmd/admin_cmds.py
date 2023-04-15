#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""user commands"""

import typing
from pprint import pprint

import awc
import awc.api
import awc.sql
import awc.sql.helpers
import pypika.queries  # type: ignore
import sqlparse  # type: ignore

from ..util import run_sql
from . import Command
from .mgr import CommandManager

ADMIN_CMDS: typing.Final[CommandManager] = CommandManager(True)

# generates automatic wrappers for some functions
for __wrap_sql in (
    awc.sql.helpers.whitelist,
    awc.sql.helpers.unwhitelist,
    awc.sql.helpers.ban,
    awc.sql.helpers.unban,
):

    def __wrap_fn(
        api: awc.Awc,
        cmd: Command,
        __sql_func: typing.Callable[
            [str], typing.List[pypika.queries.QueryBuilder]
        ] = __wrap_sql,
    ) -> int:
        run_sql(api, __sql_func(cmd.cmd))
        print(f"{__sql_func.__name__}({cmd.cmd!r}) has finished")

        return 0

    __wrap_fn.__name__ = __wrap_sql.__name__
    __wrap_fn.__doc__ = f"""{__wrap_sql.__name__} a user
usage : {__wrap_sql.__name__} <user>"""

    ADMIN_CMDS.new(ADMIN_CMDS.nonempty(__wrap_fn))


@ADMIN_CMDS.new
@ADMIN_CMDS.nonempty
def sql(api: awc.Awc, cmd: Command) -> int:
    """run sql queries ( backs up to backup.db )
    usage : sql <sql query>"""

    queries: typing.List[str] = sqlparse.split(cmd.cmd)  # type: ignore

    for query, result in zip(queries, awc.api.sql(api, queries, "backup")):
        print(f"> {query}")
        pprint(result)
        print()

    return 0


@ADMIN_CMDS.new
def togglelock(api: awc.Awc, *_: typing.Any) -> int:
    """toggle comment lock
    usage : togglelock"""

    print("lock status now :", awc.api.toggle_comment_lock(api))
    return 0


@ADMIN_CMDS.new
def getqueue(api: awc.Awc, *_: typing.Any) -> int:
    """get people in the ip queue
    usage : getqueue"""

    for row in awc.api.sql(api, awc.sql.sql(awc.sql.IpQueue.all()))[0]:
        print(
            f"""ip hash : {row[0]}
author : {row[1]}
reason : {row[2]}
"""
        )

    return 0


@ADMIN_CMDS.new
def getwhitelist(api: awc.Awc, *_: typing.Any) -> int:
    """get people in the ip whitelist
    usage : getwhitelist"""

    for row in awc.api.sql(api, awc.sql.sql(awc.sql.IpWhitelist.all()))[0]:
        print(
            f"""ip hash : {row[0]}
author : {row[1]}
"""
        )

    return 0


@ADMIN_CMDS.new
def getbans(api: awc.Awc, *_: typing.Any) -> int:
    """get people in the ban list
    usage : getbans"""

    for row in awc.api.sql(api, awc.sql.sql(awc.sql.Ban.all()))[0]:
        print(row[0])

    return 0


@ADMIN_CMDS.new
@ADMIN_CMDS.nonempty
def reject(api: awc.Awc, cmd: Command) -> int:
    """reject a user from the ip queue
    usage : reject <user>"""

    awc.api.sql(
        api,
        awc.sql.sql(
            awc.sql.delete(
                awc.sql.IpQueue.query(awc.sql.IpQueue.author == cmd.cmd)  # type: ignore
            )
        ),
    )

    print(f"rejected user's {cmd.cmd!r} application")

    return 0