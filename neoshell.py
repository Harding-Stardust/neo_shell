#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
A new and modern shell

Should work the same on Windows, Linux and Mac. Uses Jupyter-console as base

1. Om du har en lång körning på flera filer (exempel: convert *.mp4) då skall det i efterhand lätt gå att se vilka filer som är färdiga och vilka som är kvar att jobba på.
1.1 Medans denna långa körning pågår så skall det gå att gå in och ändra i kön ifall en vill prioritera om filer, ta bort eller lägga till.
2. Om du skriver ett långt kommando men inte riktigt minns hur det skall vara så kan du när som helst skriva '?' för att få hjälpen och sedan få kommandot tillbaka till prompten så du kan fortsätta skriva.
3. Det skall gå att "select multiple files" med ett kommando som t.ex. 'select *.mp4' och sedan 'select *.webm'. Dessa filer som nu är valda skall enkelt gå att se i en lista till höger. Det skall gå att ta bort filer ur den listan också.
4. Varje console skall ha en backend och en foreground så att en kan använda det som SSH samt att det går att disconnecta utan att allt du håller på med dör.
5. Snabbknappar, F1 - F12 men kanske även andra
6. Massor av "choice.com" där du har val att göra men om du inte gör något val inom 30 sekunder så väljer console åt dig.
7. Om console förstår commandot men det kräver sudo så skall du kunna bara fortsätta med sudo istället för att skriva om
8. Web interface? Fördel är att HTML har väldigt välutvecklade grafiska element.
9. Enkelt kunna pausa en lång körning och sedan ställa in när den skall fortsätta.
10. Delete file skall märka filen som "can be taken away" (lite som papperskorgen).
11. Det skall funka BRA på Windows, Linux, Mac
12. Enkelt att plugga in andra språk, som t.ex. python


# TODO: ** in glob does not work atm

# TODO: Process creation

https://docs.python.org/3/library/multiprocessing.html#module-multiprocessing

import shlex, subprocess
command_line = input()
/bin/vikings -input eggs.txt -output "spam spam.txt" -cmd "echo '$MONEY'"
args = shlex.split(command_line)
print(args)
['/bin/vikings', '-input', 'eggs.txt', '-output', 'spam spam.txt', '-cmd', "echo '$MONEY'"]
p = subprocess.Popen(args) # Success!


"""
from __future__ import annotations

__version__ = 230406205304
__author__ = "Harding"
__description__ = __doc__
__copyright__ = "Copyright 2023"
__credits__ = ["Other projects"]
__license__ = "GPL"
__maintainer__ = "Harding"
__email__ = "not.at.the.moment@example.com"
__status__ = "Development"

from typing import Union, List, Iterator, Any
import os
import pathlib
import re
import json
import time

import numpy as np
import harding_utils as hu
import inputtimeout_harding as ih

use_natsort = True
try:
    import natsort
except ImportError:
    use_natsort = False
    hu.warning_print("Module natsort not installed, this module is not required but strongly recommended. pip install natsort")

use_prettytable = True
try:
    import prettytable
except ImportError:
    use_prettytable = False
    hu.warning_print("Module prettytable not installed, this module is not required but strongly recommended. pip install prettytable")

def _repr_type_str(arg_object: Any) -> str:
    ''' Generic repr function that types the type and then the str(object) '''
    return f"{type(arg_object)} which has str(self):\n{str(arg_object)}"
_file_type = Union[str, pathlib.Path]
_file_type_extended = Union[str, pathlib.Path, List[str], List[pathlib.Path], '_files', None]
_directory_type = Union[str, pathlib.Path]
_directory_type_extended = Union[str, pathlib.Path, None]

class _files:
    _selected: List[str] = []

    def __init__(self, arg_file_pattern: _file_type_extended = None,
                       arg_recursive: bool = False,
                       arg_supress_errors: bool = False,
                       arg_debug: bool = False):
        self.select(arg_file_pattern=arg_file_pattern,
                    arg_recursive=arg_recursive,
                    arg_supress_errors=arg_supress_errors,
                    arg_debug=arg_debug)

    def clear(self) -> int:
        ''' Clears the selected files '''
        self._selected = []
        return 0

    def select(self, arg_file_pattern: _file_type_extended = None,
                     arg_recursive: bool = False,
                     arg_supress_errors: bool = False,
                     arg_debug: bool = False
                ) -> int:
        ''' Makes a new selection of files (clear the old selection) and returns the number of files added

            # TODO: If the arg_file_pattern starts with a ! then run that with os.system() and parse the result
        '''
        if arg_file_pattern is None:
            return self.clear()

        if isinstance(arg_file_pattern, _files):
            self.clear()
            self += arg_file_pattern
            return len(self)

        if isinstance(arg_file_pattern, pathlib.Path):
            arg_file_pattern = str(arg_file_pattern)

        if isinstance(arg_file_pattern, list): # TODO: I Don't like this solution. Make it nicer.
            self._selected = []
            for l_item in arg_file_pattern:
                l_new_files = hu.adv_glob(arg_paths=l_item,
                                          arg_recursive=arg_recursive,
                                          arg_supress_errors=arg_supress_errors,
                                          arg_debug=arg_debug)
                self._selected.extend(l_new_files)
            self.sort()
            return len(self)

        if isinstance(arg_file_pattern, str) and arg_file_pattern.startswith('http'):
            l_new_files = [arg_file_pattern]
        else:
            l_new_files = hu.adv_glob(arg_paths=arg_file_pattern,
                                     arg_recursive=arg_recursive,
                                     arg_supress_errors=arg_supress_errors,
                                     arg_debug=arg_debug)
        self._selected = l_new_files
        self.sort()
        return len(self)

    __call__ = select

    def sort(self, arg_sort_by: str = "alphabetical"):
        ''' Sort the files in alhpabetic order.

            TODO: Parameter arg_sort_by can be 1 of the following strings: "alphabetical", "size", "extension"

        '''
        del arg_sort_by # TODO: Not implemented yet
        self._selected = np.unique(self._selected) # type: ignore
        if use_natsort:
            self._selected = natsort.natsorted(self._selected)

    def __add__(self, arg_adding: Union[str, pathlib.Path, List[str], _files]) -> _files:
        if isinstance(arg_adding, pathlib.Path):
            arg_adding = str(arg_adding)

        if isinstance(arg_adding, (list, str)):
            _new_files = hu.adv_glob(arg_paths=arg_adding)
            self._selected.extend(_new_files)
        elif isinstance(arg_adding, _files):
            self._selected.extend(_files._selected)
        else:
            raise ValueError(f'Cannot add {type(arg_adding)}')
        return self

    def __sub__(self, arg_subing: Union[str, pathlib.Path, List[str], _files]) -> _files:
        if isinstance(arg_subing, pathlib.Path):
            arg_subing = str(arg_subing)

        if isinstance(arg_subing, (list, str)):
            _files_to_remove = hu.adv_glob(arg_paths=arg_subing)
        elif isinstance(arg_subing, _files):
            _files_to_remove = arg_subing._selected
        else:
            raise ValueError(f'Cannot sub {type(arg_subing)}')

        print(_files_to_remove)
        self._selected = [file for file in self._selected if file not in _files_to_remove]
        return self

    def add(self, arg_file_pattern: Union[str, pathlib.Path, List[str], None] = None,
                  arg_recursive: bool = False,
                  arg_supress_errors: bool = False,
                  arg_debug: bool = False) -> int:
        ''' Adds files to the selection '''
        _new_files = _files(arg_file_pattern=arg_file_pattern,
                            arg_recursive=arg_recursive,
                            arg_supress_errors=arg_supress_errors,
                            arg_debug=arg_debug)
        self += _new_files
        return len(_new_files)

    def prioritize(self, arg_file: Union[str, pathlib.Path]):
        ''' Put this file first in the list '''
        try:
            self._selected.insert(0, self._selected.pop(self._selected.index(str(arg_file))))
        except ValueError:
            hu.warning_print(f"Could NOT find the file '{arg_file}'")

    def remove_by_regexp(self, arg_regexp: str, arg_regexp_flags: int = re.IGNORECASE) -> int:
        ''' If you have a large selection of files and want to remove some of them

            Returns the number of files that matched and was removed
        '''

        try:
            _regexp = re.compile(arg_regexp, flags=arg_regexp_flags) # most useful is probable re.IGNORECASE
        except re.error as regexp_error:
            hu.log_print(f"Error in the regexp: {regexp_error}. You wrote: '{arg_regexp}'", arg_type="ERROR") # TODO: Error_print?
            return 0

        _len_before = len(self._selected)
        self._selected = [file for file in self._selected if not _regexp.fullmatch(file)]
        return _len_before - len(self._selected)

    def save_selection_to_file(self, arg_filename: Union[str, pathlib.Path, None] = None, arg_as_json: bool = False) -> bool:
        ''' Save the current file dict to a file.

            if arg_filename is None, then save a file named neoshell.files.json in the same folder
            as the first file in the file list
        '''
        if not arg_filename:
            arg_filename = os.path.join(os.path.dirname(self._selected[0]), "neoshell.files.json")

        arg_filename = str(arg_filename)
        if arg_as_json or arg_filename.endswith('.json'):
            return hu.dict_dump_to_json_file(arg_dict=self._selected, arg_filename=arg_filename)
        return hu.text_write_whole_file(arg_filename=arg_filename, arg_text='\n'.join(self._selected))

    def load_selection_from_file(self, arg_filename_or_url: Union[str, pathlib.Path]) -> int:
        ''' If you have a file saved with each row is a full file path, then this can load that.
            The saved file list can also be a valid JSON.

            Returns the number of files that is in the file dict after we loaded the file
        '''

        _whole_file = hu.text_read_whole_file(arg_filename_or_url=str(arg_filename_or_url))
        if not _whole_file:
            return self.clear()
        if self._json_set(_whole_file):
            return len(self._selected)

        hu.log_print(f"Failed to parse '{arg_filename_or_url}' as JSON", arg_type="ERROR")

        _list_split = hu.list_from_str(_whole_file, arg_re_splitter='[\n]|[\r]')
        if not _list_split:
            hu.error_print("File is not a valid file list")
            return self.clear()
        self._selected = _list_split
        return len(self._selected)

    def _json_get(self) -> str:
        return hu.dict_to_json_string_pretty(self._selected)

    def _json_set(self, arg_json: str) -> bool:
        ''' Try to parse the input str as JSON and validate that it's a list '''
        try:
            _tmp_list = json.loads(arg_json)
            if not _tmp_list or not isinstance(_tmp_list, list) or not isinstance(_tmp_list[0], str):
                hu.error_print("File is not a valid file list")
                return False
        except json.JSONDecodeError:
            return False

        self._selected = _tmp_list
        return True

    json = property(fget=_json_get, fset=_json_set, doc='Handle the selected files as a JSON str') # type: ignore

    def _table(self) -> bool:
        ''' Print the files as a table '''
        if not use_prettytable:
            hu.log_print("You do NOT have prettytable installed. pip install prettytable", arg_type="ERROR")
            return False

        _table = prettytable.PrettyTable()
        _table.field_names = ["Filename", "Size", "Created", "Modified"] # TODO: Add support for showing filesize and created date?
        _table.align["Filename"] = "l"
        _table.align["Size"] = "r"

        _table.add_rows([[file, 0, 'TODO:', 'TODO:'] for file in self._selected])
        print(f"[{hu.now_nice_format()}]")
        print(_table)
        return True

    table = property(fget=_table, doc='Show the selected files in nice table')

    def system(self, arg_command: str, arg_dry_run: bool = False) -> bool:
        ''' Run neoshell.system() Which in the end lands in os.system() on all files. Use the string %file in the command to replace this by the filename

            Set the argument arg_dry_run to True to see the commands that would be executed without actually executing them.
        '''
        return system(arg_command=arg_command, arg_files=self, arg_dry_run=arg_dry_run)

    def __len__(self) -> int:
        return len(self._selected)

    def __iter__(self) -> Iterator:
        ''' Allows for code like: for file in neoshell.files: to work '''
        return iter(self._selected)

    def __next__(self, arg_iterator: Iterator) -> str:
        ''' Allows for code like: for file in neoshell.files: to work '''
        return next(arg_iterator)

    def __str__(self) -> str:
        return self._json_get()

    def __repr__(self) -> str:
        return _repr_type_str(self)

files = _files()

class _ls:
    ''' TODO: Is this sane? '''
    _last_ls: _files = _files()

    def __init__(self, arg_pattern: Union[str, None] = None):
        del arg_pattern # TODO: Not used yet

    def list_files(self, arg_file_pattern: Union[str, pathlib.Path, List[str], None] = None,
                         arg_recursive: bool = False,
                         arg_supress_errors: bool = False,
                         arg_debug: bool = False
                   ) -> _files:
        if not arg_file_pattern:
            arg_file_pattern = '*'
        self._last_ls.select(arg_file_pattern=arg_file_pattern, arg_recursive=arg_recursive, arg_supress_errors=arg_supress_errors, arg_debug=arg_debug)
        print(str(self._last_ls))
        return self._last_ls

    __call__ = list_files


    def __repr__(self) -> str:
        _in_jupyter = False
        try:
            info = hu._file_and_line_number(18)
            function_name = f"{os.path.splitext(os.path.basename(info.filename))[0]}.{info.function}"
            _in_jupyter = function_name == "ipkernel.do_execute"
            if _in_jupyter:
                hu.log_print("We are in Jupyter")
        except IndexError:
            hu.log_print("We are NOT in Jupyter")

        hu.timestamped_print(f"cwd: {cwd()}")
        self.list_files()







        self._last_ls = _files('asdasda')
        return "\n".join(self._last_ls)
ls = _ls()

def cwd(arg_new_current_working_directory: _directory_type_extended = None) -> pathlib.Path:
    ''' Gets (or sets) the current working directory '''
    if arg_new_current_working_directory:
        if isinstance(arg_new_current_working_directory, str):
            arg_new_current_working_directory = pathlib.Path(arg_new_current_working_directory)
            arg_new_current_working_directory = arg_new_current_working_directory.expanduser()


        os.chdir(str(arg_new_current_working_directory))
    return pathlib.Path.cwd()

cd = cwd # TODO: Is this a bad idea? Linux user will not like that cd doesn't take them to home. Make it a config

def system(arg_command: str, arg_files: _file_type_extended = None, arg_dry_run: bool = False) -> bool:
    ''' Run the command in the OS with the os.system()

        # TODO: Allow for a List[str] to be passed as arg_command?
    '''
    if '%file' in arg_command:
        if not arg_files:
            hu.warning_print(f"No selected files, suggested files are the ones in the current working directory: {cwd()}")
            l_files = _files('*.*')
            hu.timestamped_print(str(l_files))
            _t = ih.inputtimeout(arg_prompt=hu.timestamped_line('Is this OK? [Y/n]'), arg_timeout_in_seconds=30.0, arg_default_return_value='Y')
            suggestion_ok = _t == '' or _t.lower().startswith('y')
            hu.timestamped_print(f"It was OK: {suggestion_ok}")
            if not suggestion_ok:
                return False
        elif isinstance(arg_files, _files):
            l_files = arg_files
        else:
            l_files = _files(arg_files)

        if not l_files:
            hu.error_print("No files selected")
            return False

        hu.timestamped_print("Going to run the following commands:")
        index = 0
        for file in l_files:
            _command = arg_command.replace('%file', f'"{file}"')
            print(f"[{index:02d}] {hu.console_color(_command, arg_color='OKBLUE')}")
            index += 1

        time.sleep(0.01)
        all_ok = True
        for file in l_files:
            _command = arg_command.replace('%file', f'"{file}"')
            all_ok = all_ok and system(arg_command=_command, arg_dry_run=arg_dry_run)

        return all_ok

    hu.timestamped_print(f"Running command:  {hu.console_color(arg_command, arg_color='OKBLUE')}", arg_force_flush=True)
    time.sleep(0.01)
    if not arg_dry_run:
        os.system(arg_command)
    return True # TODO: See if we can make a smarter return value depending on what os.system() returned

def home() -> pathlib.Path:
    ''' Get the users home directory '''
    return pathlib.Path.home()

def exists(arg_path: Union[str, pathlib.Path]) -> bool:
    ''' Return true if the file/directory exists '''
    return pathlib.Path(arg_path).exists()

def rename_files_to_good_names(arg_files: _file_type_extended, arg_debug: bool = False) -> bool:
    ''' Rename files to something that is OS safe. See harding_utils.smart_filesystem_safe_path()
    # TODO: This function is not working
    '''
    if not arg_files:
        hu.error_print("arg_files is NOT a valid file list")
        return False

    l_files = _files(arg_files) # TODO: Make sure that the _files ctor can handle all kinds of weird input
    hu.log_print(l_files, arg_debug)
    for l_file in l_files:
        l_file = l_file.lower() # TODO: Linux vs Windows in case sensitive filenames? YIKES
        l_better_filename: str = hu.smart_filesystem_safe_path(l_file).lower()
        if l_file == l_better_filename:
            print(f"{l_file} is a good name!")
        else:
            print(f"Rename {l_file} --> {l_better_filename}")



# TODO: def copy()
# TODO: def move()
# TODO: def dir() # Det skall gå att hänvisa till en ls för att lägga till i selected
# TODO: def del()
# TODO: def os.system()

if __name__ == "__main__":
    print("This is part of neoshell and is not suppose to be used from the command line")
