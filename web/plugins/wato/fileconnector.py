# -*- encoding: utf-8; py-indent-offset: 4 -*-

# +------------------------------------------------------------+
# |                                                            |
# |             | |             | |            | |             |
# |          ___| |__   ___  ___| | ___ __ ___ | | __          |
# |         / __| '_ \ / _ \/ __| |/ / '_ ` _ \| |/ /          |
# |        | (__| | | |  __/ (__|   <| | | | | |   <           |
# |         \___|_| |_|\___|\___|_|\_\_| |_| |_|_|\_\          |
# |                                   custom code by SVA       |
# |                                                            |
# +------------------------------------------------------------+
#
# File Connector is a no-code DCD connector for checkmk.
#
# Copyright (C) 2021-2022 SVA System Vertrieb Alexander GmbH
#                         Niko Wenselowski <niko.wenselowski@sva.de>

# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
"""
WATO configuration module for File Connector.
"""

import os.path

from cmk.gui.cee.plugins.wato.dcd import (  # noqa: F401 # pylint: disable=unused-import,import-error
    connector_parameters_registry, ConnectorParameters,
)

from cmk.gui.exceptions import MKUserError  # pylint: disable=import-error

from cmk.gui.i18n import _  # pylint: disable=import-error

from cmk.gui.plugins.wato import FullPathFolderChoice  # pylint: disable=import-error

from cmk.gui.valuespec import (  # pylint: disable=import-error
    Age,
    Alternative,
    Checkbox,
    Dictionary,
    Filename,
    FixedValue,
    Integer,
    ListOfStrings,
    RegExpUnicode,
    TextInput,
)


@connector_parameters_registry.register
class FileConnectorParameters(ConnectorParameters):  # pylint: disable=missing-class-docstring

    @classmethod
    def name(cls) -> str:  # pylint: disable=missing-function-docstring
        return "fileconnector"

    @classmethod
    def title(cls) -> str:  # pylint: disable=missing-function-docstring
        return _("File import")

    @classmethod
    def description(cls) -> str:  # pylint: disable=missing-function-docstring
        return _("Connector for importing hosts from a CSV, JSON or BVQ file.")

    def valuespec(self):  # pylint: disable=missing-function-docstring
        csv_value = FixedValue(value="csv", title="CSV", totext="Comma-separated values.")
        bvq_value = FixedValue(value="bvq", title="BVQ", totext="Export from a BVQ system.")
        json_value = FixedValue(value="json", title="JSON", totext="File with JSON format.")

        return Dictionary(
            elements=[
                ("interval", Age(
                    title=_("Sync interval"),
                    minvalue=1,
                    default_value=300,
                )),
                ("path", Filename(
                    title=_("Path of the file to import."),
                    help=_("This is the absolute path to the file. "
                           "In CSV format the first column of the "
                           "file is assumed to contain the hostname."),
                    allow_empty=False,
                    validate=self.validate_csv,
                )),
                ("file_format", Alternative(
                    title=_("Data Format"),
                    elements=[csv_value, json_value, bvq_value],
                    default_value=csv_value,
                    help=_(
                        "Select the data format for the file."
                    ),
                )),
                ("csv_delimiter", TextInput(
                    title=_("CSV delimiter"),
                    default_value=",",
                    help=_(
                        "The delimiter used to separate fields in a csv file."
                    ),
                )),
                ("folder", FullPathFolderChoice(
                    title=_("Create hosts in"),
                    help=_("All hosts created by this connection will be "
                           "placed in this folder. You are free to move the "
                           "host to another folder after creation."),
                )),
                ("host_filters", ListOfStrings(
                    title=_("Only add matching hosts"),
                    help=_(
                        "Only care about hosts with names that match one of these "
                        "regular expressions."),
                    orientation="horizontal",
                    valuespec=RegExpUnicode(mode=RegExpUnicode.prefix,),
                )),
                ("host_overtake_filters", ListOfStrings(
                    title=_("Take over existing hosts"),
                    help=_(
                        "Take over already existing hosts with names that "
                        "match one of these regular expressions. This will "
                        "not take over hosts handled by foreign connections "
                        "or plugins. Hosts that have been took over will be "
                        "deleted once they vanish from the import file."),
                    orientation="horizontal",
                    valuespec=RegExpUnicode(mode=RegExpUnicode.prefix,),
                )),
                ("chunk_size", Integer(
                    default_value=0,
                    minvalue=0,
                    title=_("Chunk size"),
                    help=_(
                        "Split processing of hosts into smaller parts of the "
                        "given size. "
                        "After each part is processed an activation of the "
                        "changes is triggered. "
                        "This setting can reduce performance impacts "
                        "when working with large change sets. "
                        "Setting it to 0 disables splitting."),
                )),
                ("use_service_discovery", Checkbox(
                    default_value=True,
                    title=_("Use service discovery"),
                    help=_(
                        "Controls if service discovery is triggered for new hosts."
                    ),
                )),
                ("label_prefix", TextInput(
                    title=_("Label prefix"),
                    default_value="dcd/",
                    help=_(
                        "This prefix will be attached to labels that "
                        "come from the import file. "
                        "If a prefix is set only labels matching the "
                        "prefix will be managed by this plugin. "
                        "The prefix will not be taken into account "
                        "for path creation if a path template is set."
                    ),
                )),
                ("label_path_template", TextInput(
                    title=_("Use labels to organize hosts"),
                    label=_("Path template"),
                    default_value="location/org",
                    help=_(
                        "Controls if the placement of a host in the "
                        "folder structure is based on the labels of "
                        "the host. "
                        "If this is activated the folder selected "
                        "under 'create hosts in' will act as a prefix "
                        "for the path. "
                        "Separate folders through a single forward "
                        "slash (/). "
                    ),
                    validate=self.validate_label_path_template,
                )),
                ("lowercase_everything", Checkbox(
                    default_value=False,
                    title=_("Lowercase everything"),
                    help=_(
                        "This results in all imported data being lowercased."
                    ),
                )),
                ("replace_special_chars", Checkbox(
                    default_value=False,
                    title=_("Replace characters to improve API compability"),
                    help=_(
                        "Replaces characters that might cause problems when"
                        "used with the REST API by an underscore."
                    ),
                )),
            ],
            optional_keys=[
                "host_filters",
                "host_overtake_filters",
                "chunk_size",
                "label_path_template",
                "csv_delimiter",
                "label_prefix",
            ],
        )

    @staticmethod
    def validate_csv(filename, varprefix):  # pylint: disable=missing-function-docstring
        if not os.path.isfile(filename):
            raise MKUserError(varprefix, f"No file {filename}")

    @staticmethod
    def validate_label_path_template(template, varprefix):  # pylint: disable=missing-function-docstring
        if not template.islower():
            raise MKUserError(varprefix, "Please supply only lowercase variables!")

        if template.strip() != template:
            raise MKUserError(varprefix, "Path template can not start or end with whitespace!")

        if template.startswith('/'):
            raise MKUserError(varprefix, "Do not start with a slash!")

        if template.endswith('/'):
            raise MKUserError(varprefix, "Do not specify a slash as last element!")

        if '' in [folder.strip() for folder in template.split('/')]:
            raise MKUserError(varprefix, "Do not use empty values!")

        if '' in template.split('/'):
            raise MKUserError(varprefix, "Do not use double slashes!")
