#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Part of RedELK

This connector sends RedELK alerts via Mattermost

Authors:
- Bryan De Houwer (@nurfed1)
"""
import logging
import requests
from modules.helpers import get_value, pprint
import config

info = {
    "version": 0.1,
    "name": "mattermost connector",
    "description": "This connector sends RedELK alerts via Mattermost",
    "type": "redelk_connector",
    "submodule": "mattermost",
}


class Module:  # pylint: disable=too-few-public-methods
    """mattermost connector module"""

    def __init__(self):
        self.logger = logging.getLogger(info["submodule"])

    def send_alarm(self, alarm):
        """Send the alarm notification"""
        description = alarm["info"]["description"]
        if len(alarm["groupby"]) > 0:
            description += f'\n _Please note that the items below have been grouped by: {alarm["groupby"]}_'

        fields = []
        try:
            for hit in alarm["hits"]["hits"]:
                i = 0
                title = hit["_id"]
                while i < len(alarm["groupby"]):
                    val = get_value(f'_source.{alarm["groupby"][i]}', hit)
                    if i == 0:
                        title = val
                    else:
                        title = f"{title} / {val}"
                    i += 1

                text = ""
                for field in alarm["fields"]:
                    val = get_value(f"_source.{field}", hit)

                    # Add a tab to every line of values, this makes it easier to read
                    pretty_val = "\n\t".join(pprint(val).split("\n"))
                    pretty_val += "\n"

                    text += f"**{field}**: {pretty_val}"

                fields.append({
                    "short": False,
                    "title": f"Alarm on item: {title}",
                    "value": text
                })
            # pylint: disable=broad-except
        except Exception as error:
            self.logger.exception(error)

        title = f'[{config.project_name}] Alarm from {alarm["info"]["name"]} [{alarm["hits"]["total"]} hits]'
        data = {
            "attachments": [
                {
                    "fallback": title,
                    "color": "#FF0000",
                    "title": title,
                    "text": description,
                    "fields": fields,
                }
            ]
        }

        res = requests.post(config.notifications["mattermost"]["webhook_url"], json=data, timeout=30)

        if res.status_code != 200:
            self.logger.error(
                "Informing mattermost failed: %s %s", res.status_code, res.text
            )
            self.logger.error(alarm)
