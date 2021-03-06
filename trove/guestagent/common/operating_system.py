# Copyright (c) 2011 OpenStack Foundation
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import inspect
import operator
import os
import re
import stat
import tempfile

from functools import reduce
from oslo_concurrency.processutils import UnknownArgumentError

from trove.common import exception
from trove.common.i18n import _
from trove.common.stream_codecs import IdentityCodec
from trove.common import utils

REDHAT = 'redhat'
DEBIAN = 'debian'
SUSE = 'suse'


def read_file(path, codec=IdentityCodec(), as_root=False):
    """
    Read a file into a Python data structure
    digestible by 'write_file'.

    :param path             Path to the read config file.
    :type path              string

    :param codec:           A codec used to deserialize the data.
    :type codec:            StreamCodec

    :returns:               A dictionary of key-value pairs.

    :param as_root:         Execute as root.
    :type as_root:          boolean

    :raises:                :class:`UnprocessableEntity` if file doesn't exist.
    :raises:                :class:`UnprocessableEntity` if codec not given.
    """
    if path and os.path.exists(path):
        if as_root:
            return _read_file_as_root(path, codec)
        with open(path, 'r') as fp:
            return codec.deserialize(fp.read())

    raise exception.UnprocessableEntity(_("File does not exist: %s") % path)


def _read_file_as_root(path, codec):
    """Read a file as root.

    :param path                Path to the written file.
    :type path                 string

    :param codec:              A codec used to serialize the data.
    :type codec:               StreamCodec
    """
    with tempfile.NamedTemporaryFile() as fp:
        copy(path, fp.name, force=True, as_root=True)
        chmod(fp.name, FileMode.ADD_READ_ALL(), as_root=True)
        return codec.deserialize(fp.read())


def write_file(path, data, codec=IdentityCodec(), as_root=False):
    """Write data into file using a given codec.
    Overwrite any existing contents.
    The written file can be read back into its original
    form by 'read_file'.

    :param path                Path to the written config file.
    :type path                 string

    :param data:               An object representing the file contents.
    :type data:                object

    :param codec:              A codec used to serialize the data.
    :type codec:               StreamCodec

    :param codec:              Execute as root.
    :type codec:               boolean

    :raises:                   :class:`UnprocessableEntity` if path not given.
    """
    if path:
        if as_root:
            _write_file_as_root(path, data, codec)
        else:
            with open(path, 'w', 0) as fp:
                fp.write(codec.serialize(data))
    else:
        raise exception.UnprocessableEntity(_("Invalid path: %s") % path)


def _write_file_as_root(path, data, codec):
    """Write a file as root. Overwrite any existing contents.

    :param path                Path to the written file.
    :type path                 string

    :param data:               An object representing the file contents.
    :type data:                StreamCodec

    :param codec:              A codec used to serialize the data.
    :type codec:               StreamCodec
    """
    # The files gets removed automatically once the managing object goes
    # out of scope.
    with tempfile.NamedTemporaryFile('w', 0, delete=False) as fp:
        fp.write(codec.serialize(data))
        fp.close()  # Release the resource before proceeding.
        copy(fp.name, path, force=True, as_root=True)


class FileMode(object):
    """
    Represent file permissions (or 'modes') that can be applied on a filesystem
    path by functions such as 'chmod'. The way the modes get applied
    is generally controlled by the operation ('reset', 'add', 'remove')
    group to which they belong.
    All modes are represented as octal numbers. Modes are combined in a
    'bitwise OR' (|) operation.
    Multiple modes belonging to a single operation are combined
    into a net value for that operation which can be retrieved by one of the
    'get_*_mode' methods.
    Objects of this class are compared by the net values of their
    individual operations.

    :seealso: chmod

    :param reset:            List of (octal) modes that will be set,
                             other bits will be cleared.
    :type reset:             list

    :param add:              List of (octal) modes that will be added to the
                             current mode.
    :type add:               list

    :param remove:           List of (octal) modes that will be removed from
                             the current mode.
    :type remove:            list
    """

    @classmethod
    def SET_FULL(cls):
        return cls(reset=[stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO])  # =0777

    @classmethod
    def SET_GRP_RW_OTH_R(cls):
        return cls(reset=[stat.S_IRGRP | stat.S_IWGRP | stat.S_IROTH])  # =0064

    @classmethod
    def SET_USR_RO(cls):
        return cls(reset=[stat.S_IRUSR])  # =0400

    @classmethod
    def SET_USR_RW(cls):
        return cls(reset=[stat.S_IRUSR | stat.S_IWUSR])  # =0600

    @classmethod
    def ADD_READ_ALL(cls):
        return cls(add=[stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH])  # +0444

    @classmethod
    def ADD_GRP_RW(cls):
        return cls(add=[stat.S_IRGRP | stat.S_IWGRP])  # +0060

    def __init__(self, reset=None, add=None, remove=None):
        self._reset = list(reset) if reset is not None else []
        self._add = list(add) if add is not None else []
        self._remove = list(remove) if remove is not None else []

    def get_reset_mode(self):
        """Get the net (combined) mode that will be set.
        """
        return self._combine_modes(self._reset)

    def get_add_mode(self):
        """Get the net (combined) mode that will be added.
        """
        return self._combine_modes(self._add)

    def get_remove_mode(self):
        """Get the net (combined) mode that will be removed.
        """
        return self._combine_modes(self._remove)

    def _combine_modes(self, modes):
        return reduce(operator.or_, modes) if modes else None

    def has_any(self):
        """Check if any modes are specified.
        """
        return bool(self._reset or self._add or self._remove)

    def __hash__(self):
        return hash((self.get_reset_mode(),
                     self.get_add_mode(),
                     self.get_remove_mode()))

    def __eq__(self, other):
        if other and isinstance(other, FileMode):
            if other is self:
                return True

            return (other.get_reset_mode() == self.get_reset_mode() and
                    other.get_add_mode() == self.get_add_mode() and
                    other.get_remove_mode() == self.get_remove_mode())

        return False

    def __repr__(self):
        args = []
        if self._reset:
            args.append('reset=[{:03o}]'.format(self.get_reset_mode()))
        if self._add:
            args.append('add=[{:03o}]'.format(self.get_add_mode()))
        if self._remove:
            args.append('remove=[{:03o}]'.format(self.get_remove_mode()))

        return 'Modes({:s})'.format(', '.join(args))


def get_os():
    if os.path.isfile("/etc/redhat-release"):
        return REDHAT
    elif os.path.isfile("/etc/SuSE-release"):
        return SUSE
    else:
        return DEBIAN


def file_discovery(file_candidates):
    for file in file_candidates:
        if os.path.isfile(file):
            return file


def start_service(service_candidates):
    _execute_service_command(service_candidates, 'cmd_start')


def stop_service(service_candidates):
    _execute_service_command(service_candidates, 'cmd_stop')


def enable_service_on_boot(service_candidates):
    _execute_service_command(service_candidates, 'cmd_enable')


def disable_service_on_boot(service_candidates):
    _execute_service_command(service_candidates, 'cmd_disable')


def _execute_service_command(service_candidates, command_key):
    """
    :param service_candidates        List of possible system service names.
    :type service_candidates         list

    :param command_key               One of the actions returned by
                                     'service_discovery'.
    :type command_key                string

    :raises:          :class:`UnprocessableEntity` if no candidate names given.
    :raises:          :class:`RuntimeError` if command not found.
    """
    if service_candidates:
        service = service_discovery(service_candidates)
        if command_key in service:
            utils.execute_with_timeout(service[command_key], shell=True)
        else:
            raise RuntimeError(_("Service control command not available: %s")
                               % command_key)
    else:
        raise exception.UnprocessableEntity(_("Candidate service names not "
                                              "specified."))


def service_discovery(service_candidates):
    """
    This function discovers how to start, stop, enable and disable services
    in the current environment. "service_candidates" is an array with possible
    system service names. Works for upstart, systemd, sysvinit.
    """
    result = {}
    for service in service_candidates:
        result['service'] = service
        # check upstart
        if os.path.isfile("/etc/init/%s.conf" % service):
            result['type'] = 'upstart'
            # upstart returns error code when service already started/stopped
            result['cmd_start'] = "sudo start %s || true" % service
            result['cmd_stop'] = "sudo stop %s || true" % service
            result['cmd_enable'] = ("sudo sed -i '/^manual$/d' "
                                    "/etc/init/%s.conf" % service)
            result['cmd_disable'] = ("sudo sh -c 'echo manual >> "
                                     "/etc/init/%s.conf'" % service)
            break
        # check sysvinit
        if os.path.isfile("/etc/init.d/%s" % service):
            result['type'] = 'sysvinit'
            result['cmd_start'] = "sudo service %s start" % service
            result['cmd_stop'] = "sudo service %s stop" % service
            if os.path.isfile("/usr/sbin/update-rc.d"):
                result['cmd_enable'] = "sudo update-rc.d %s defaults; sudo " \
                                       "update-rc.d %s enable" % (service,
                                                                  service)
                result['cmd_disable'] = "sudo update-rc.d %s defaults; sudo " \
                                        "update-rc.d %s disable" % (service,
                                                                    service)
            elif os.path.isfile("/sbin/chkconfig"):
                result['cmd_enable'] = "sudo chkconfig %s on" % service
                result['cmd_disable'] = "sudo chkconfig %s off" % service
            break
        # check systemd
        service_path = "/lib/systemd/system/%s.service" % service
        if os.path.isfile(service_path):
            result['type'] = 'systemd'
            result['cmd_start'] = "sudo systemctl start %s" % service
            result['cmd_stop'] = "sudo systemctl stop %s" % service

            # currently "systemctl enable" doesn't work for symlinked units
            # as described in https://bugzilla.redhat.com/1014311, therefore
            # replacing a symlink with its real path
            if os.path.islink(service_path):
                real_path = os.path.realpath(service_path)
                unit_file_name = os.path.basename(real_path)
                result['cmd_enable'] = ("sudo systemctl enable %s" %
                                        unit_file_name)
                result['cmd_disable'] = ("sudo systemctl disable %s" %
                                         unit_file_name)
            else:
                result['cmd_enable'] = "sudo systemctl enable %s" % service
                result['cmd_disable'] = "sudo systemctl disable %s" % service
            break

    return result


def create_directory(dir_path, user=None, group=None, force=True, **kwargs):
    """Create a given directory and update its ownership
    (recursively) to the given user and group if any.

    seealso:: _execute_shell_cmd for valid optional keyword arguments.

    :param dir_path:        Path to the created directory.
    :type dir_path:         string

    :param user:            Owner.
    :type user:             string

    :param group:           Group.
    :type group:            string

    :param force:           No error if existing, make parent directories
                            as needed.
    :type force:            boolean

    :raises:                :class:`UnprocessableEntity` if dir_path not given.
    """

    if dir_path:
        _create_directory(dir_path, force, **kwargs)
        if user or group:
            chown(dir_path, user, group, **kwargs)
    else:
        raise exception.UnprocessableEntity(
            _("Cannot create a blank directory."))


def chown(path, user, group, recursive=True, force=False, **kwargs):
    """Changes the owner and group of a given file.

    seealso:: _execute_shell_cmd for valid optional keyword arguments.

    :param path:         Path to the modified file.
    :type path:          string

    :param user:         Owner.
    :type user:          string

    :param group:        Group.
    :type group:         string

    :param recursive:    Operate on files and directories recursively.
    :type recursive:     boolean

    :param force:        Suppress most error messages.
    :type force:         boolean

    :raises:             :class:`UnprocessableEntity` if path not given.
    :raises:             :class:`UnprocessableEntity` if owner/group not given.
    """

    if not path:
        raise exception.UnprocessableEntity(
            _("Cannot change ownership of a blank file or directory."))
    if not user and not group:
        raise exception.UnprocessableEntity(
            _("Please specify owner or group, or both."))

    owner_group_modifier = _build_user_group_pair(user, group)
    options = (('f', force), ('R', recursive))
    _execute_shell_cmd('chown', options, owner_group_modifier, path, **kwargs)


def _build_user_group_pair(user, group):
    return "%s:%s" % tuple((v if v else '') for v in (user, group))


def _create_directory(dir_path, force=True, **kwargs):
    """Create a given directory.

    :param dir_path:        Path to the created directory.
    :type dir_path:         string

    :param force:           No error if existing, make parent directories
                            as needed.
    :type force:            boolean
    """

    options = (('p', force),)
    _execute_shell_cmd('mkdir', options, dir_path, **kwargs)


def chmod(path, mode, recursive=True, force=False, **kwargs):
    """Changes the mode of a given file.

    :seealso: Modes for more information on the representation of modes.
    :seealso: _execute_shell_cmd for valid optional keyword arguments.

    :param path:            Path to the modified file.
    :type path:             string

    :param mode:            File permissions (modes).
                            The modes will be applied in the following order:
                            reset (=), add (+), remove (-)
    :type mode:             FileMode

    :param recursive:       Operate on files and directories recursively.
    :type recursive:        boolean

    :param force:           Suppress most error messages.
    :type force:            boolean

    :raises:                :class:`UnprocessableEntity` if path not given.
    :raises:                :class:`UnprocessableEntity` if no mode given.
    """

    if path:
        options = (('f', force), ('R', recursive))
        shell_modes = _build_shell_chmod_mode(mode)
        _execute_shell_cmd('chmod', options, shell_modes, path, **kwargs)
    else:
        raise exception.UnprocessableEntity(
            _("Cannot change mode of a blank file."))


def _build_shell_chmod_mode(mode):
    """
    Build a shell representation of given mode.

    :seealso: Modes for more information on the representation of modes.

    :param mode:            File permissions (modes).
    :type mode:             FileModes

    :raises:                :class:`UnprocessableEntity` if no mode given.

    :returns: Following string for any non-empty modes:
              '=<reset mode>,+<add mode>,-<remove mode>'
    """

    # Handle methods passed in as constant fields.
    if inspect.ismethod(mode):
        mode = mode()

    if mode and mode.has_any():
        text_modes = (('=', mode.get_reset_mode()),
                      ('+', mode.get_add_mode()),
                      ('-', mode.get_remove_mode()))
        return ','.join(
            ['{0:s}{1:03o}'.format(item[0], item[1]) for item in text_modes
             if item[1]])
    else:
        raise exception.UnprocessableEntity(_("No file mode specified."))


def remove(path, force=False, recursive=True, **kwargs):
    """Remove a given file or directory.

    :seealso: _execute_shell_cmd for valid optional keyword arguments.

    :param path:            Path to the removed file.
    :type path:             string

    :param force:           Ignore nonexistent files.
    :type force:            boolean

    :param recursive:       Remove directories and their contents recursively.
    :type recursive:        boolean

    :raises:                :class:`UnprocessableEntity` if path not given.
    """

    if path:
        options = (('f', force), ('R', recursive))
        _execute_shell_cmd('rm', options, path, **kwargs)
    else:
        raise exception.UnprocessableEntity(_("Cannot remove a blank file."))


def move(source, destination, force=False, **kwargs):
    """Move a given file or directory to a new location.
    Move attempts to preserve the original ownership, permissions and
    timestamps.

    :seealso: _execute_shell_cmd for valid optional keyword arguments.

    :param source:          Path to the source location.
    :type source:           string

    :param destination:     Path to the destination location.
    :type destination:      string

    :param force:           Do not prompt before overwriting.
    :type force:            boolean

    :raises:                :class:`UnprocessableEntity` if source or
                            destination not given.
    """

    if not source:
        raise exception.UnprocessableEntity(_("Missing source path."))
    elif not destination:
        raise exception.UnprocessableEntity(_("Missing destination path."))

    options = (('f', force),)
    _execute_shell_cmd('mv', options, source, destination, **kwargs)


def copy(source, destination, force=False, preserve=False, recursive=True,
         **kwargs):
    """Copy a given file or directory to another location.
    Copy does NOT attempt to preserve ownership, permissions and timestamps
    unless the 'preserve' option is enabled.

    :seealso: _execute_shell_cmd for valid optional keyword arguments.

    :param source:          Path to the source location.
    :type source:           string

    :param destination:     Path to the destination location.
    :type destination:      string

    :param force:           If an existing destination file cannot be
                            opened, remove it and try again.
    :type force:            boolean

    :param preserve:        Preserve mode, ownership and timestamps.
    :type preserve:         boolean

    :param recursive:       Copy directories recursively.
    :type recursive:        boolean

    :raises:                :class:`UnprocessableEntity` if source or
                            destination not given.
    """

    if not source:
        raise exception.UnprocessableEntity(_("Missing source path."))
    elif not destination:
        raise exception.UnprocessableEntity(_("Missing destination path."))

    options = (('f', force), ('p', preserve), ('R', recursive))
    _execute_shell_cmd('cp', options, source, destination, **kwargs)


def get_bytes_free_on_fs(path):
    """
    Returns the number of bytes free for the filesystem that path is on
    """
    v = os.statvfs(path)
    return v.f_bsize * v.f_bavail


def _execute_shell_cmd(cmd, options, *args, **kwargs):
    """Execute a given shell command passing it
    given options (flags) and arguments.

    Takes optional keyword arguments:
    :param as_root:        Execute as root.
    :type as_root:         boolean

    :param timeout:        Number of seconds if specified,
                           default if not.
                           There is no timeout if set to None.
    :type timeout:         integer

    :raises:               class:`UnknownArgumentError` if passed unknown args.
    """

    exec_args = {}
    if kwargs.pop('as_root', False):
        exec_args['run_as_root'] = True
        exec_args['root_helper'] = 'sudo'

    if 'timeout' in kwargs:
        exec_args['timeout'] = kwargs.pop('timeout')

    if kwargs:
        raise UnknownArgumentError(_("Got unknown keyword args: %r") % kwargs)

    cmd_flags = _build_command_options(options)
    cmd_args = cmd_flags + list(args)
    utils.execute_with_timeout(cmd, *cmd_args, **exec_args)


def _build_command_options(options):
    """Build a list of flags from given pairs (option, is_enabled).
    Each option is prefixed with a single '-'.
    Include only options for which is_enabled=True.
    """

    return ['-' + item[0] for item in options if item[1]]


def list_files_in_directory(root_dir, recursive=False, pattern=None):
    """
    Return absolute paths to all files in a given root directory.

    :param root_dir            Path to the root directory.
    :type root_dir             string

    :param recursive           Also probe subdirectories if True.
    :type recursive            boolean

    :param pattern             Return only files matching the pattern.
    :type pattern              string
    """
    return {os.path.abspath(os.path.join(root, name))
            for (root, _, files) in os.walk(root_dir, topdown=True)
            if recursive or (root == root_dir)
            for name in files
            if not pattern or re.match(pattern, name)}
