#!/usr/bin/env python2

"""Gui for usability."""

from FindDuplicates import Scanner, Updater
from tkFileDialog import askdirectory
from os import remove
import time
import Queue
import os.path
# Fixme, hideous tkinter import!
from Tkinter import Button, CENTER, E, END, Frame, Label, LabelFrame, \
    Listbox, MULTIPLE, N, S, StringVar, W

class DuplicatesApp(Frame):
    """Gui for usability."""

    def __init__(self, master=None):
        """__init__."""
        Frame.__init__(self, master)
        self.grid(sticky=N + S + E + W)
        self._duplicates = []

        ### create_widgets.
        # Stretching
        top = self.winfo_toplevel()
        top.rowconfigure(0, weight=1)
        top.columnconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.columnconfigure(2, weight=1)

        # frame
        self._frame = Frame(self)
        self._frame.pack_propagate(0)
        self._frame.grid(row=7, column=0, columnspan=3)

        # labels
        self.dir_label = LabelFrame(self, text='Select directory path:')
        self.dir_label.grid(
            row=0,
            column=0,
            columnspan=2,
            padx=5,
            sticky=N +
            W +
            E)

        self.path = StringVar()
        self.path.set('')
        self.path_label = Label(self.dir_label, textvariable=self.path)
        self.path_label.grid(row=0, column=0, sticky=W)

        self._result_total_var = StringVar()
        self._result_total_var.set((
            'Select directory, scan it, step through '
            'results and delete duplicate files!'
        ))
        self.result_total_label = Label(
            self,
            anchor=CENTER,
            textvariable=self._result_total_var)
        self.result_total_label.grid(row=2, column=0, columnspan=3, padx=5)

        self._result_current_label = StringVar()
        self._result_current_label.set('No results yet!')
        self.result_current_label = Label(
            self._frame,
            anchor=CENTER,
            textvariable=self._result_current_label)
        self.result_current_label.grid(row=0, column=1, padx=5)

        # listbox
        self.scan_output = Listbox(self, selectmode=MULTIPLE, width=100)
        self.scan_output.grid(
            row=3,
            column=0,
            columnspan=3,
            padx=5,
            pady=5,
            sticky=N +
            E +
            S +
            W)

        # buttons
        self.browse = Button(
            self,
            text="Browse directory",
            command=self.open_browse_dialog)
        self.browse.grid(row=0, column=2, pady=10, padx=5, sticky=E + W)

        self.scan_btn = Button(
            self,
            text="Scan directory",
            command=self.start_scan)
        self.scan_btn.grid(row=1, column=0, columnspan=3, padx=5, sticky=E + W)

        self.prev_btn = Button(
            self,
            text="Previous",
            command=self.prev_duplicate,
            width=12)
        self.prev_btn.grid(row=7, column=0, padx=5, sticky=E + W)

        self.next_btn = Button(self, text="Next", command=self.next_duplicate)
        self.next_btn.grid(row=7, column=2, padx=5, sticky=E + W)

        self.delete_btn = Button(
            self,
            text="Delete selected files",
            command=self.delete_file)
        self.delete_btn.grid(
            row=8,
            column=0,
            columnspan=3,
            padx=5,
            pady=5,
            sticky=E + W)
        self.set_start_state()
        self._root = ''
        self._time_duration = time

    def set_root(self, dirname):
        """set_root."""
        self.path.set(dirname)

    def set_start_state(self):
        """set_start_state."""
        del self._duplicates[:]
        self._duplicate_index = 0
        # needs to be a list instead of Boolean, cause it is used as a
        # reference in the threads
        self._finished_scan = [0]
        self.update_output()

    def start_scan(self):
        """start_scan."""
        if os.path.exists(self.path.get()):
            _path = self.path.get()
        else:
            self._result_total_var.set('Choose valid path!')
            return
        self._result_total_var.set('Scanning directories...please wait.')
        self.set_start_state()
        _queue = Queue.Queue()
        self._time_duration = time.time()

        scanner = Scanner(_path, _queue, self._finished_scan)
        scanner.start()

        updater = Updater(
            _queue,
            self._duplicates,
            self.update_output,
            self._finished_scan,
            self._time_duration)
        updater.start()

    def delete_file(self):
        """delete_file."""
        selection = self.scan_output.curselection()
        selection_array = []
        for item in selection:
            selection_array.append(int(item))
        for select in selection:
            del_path = self._duplicates[self._duplicate_index][int(select)]
            remove(del_path)
        # ugly, but necessary, otherwise indices of selection_array would
        # change by deleting smaller index first.
        selection_array.reverse()
        for select in selection_array:
            del self._duplicates[self._duplicate_index][select]
        self.update_output()

    def update_output(self):
        """update_output."""
        self.scan_output.delete(0, self.scan_output.size())
        if len(self._duplicates) == 0:
            if self._finished_scan[0] == 1:
                self._result_total_var.set(
                    "Finished scanning!".format(len(self._duplicates)))
                self._result_current_label.set(
                    "No duplicates found!".format(
                        self._duplicate_index + 1, len(self._duplicates))
                    )
            return
        if self._duplicate_index < 0:
            self._duplicate_index = 0
        if self._duplicate_index > len(self._duplicates) - 1:
            self._duplicate_index = len(self._duplicates) - 1
        for item in self._duplicates[self._duplicate_index]:
            self.scan_output.insert(END, item)
        self._result_total_var.set((
            "The directory contains {0} file(s)"
            " which seem to exist twice or more!"
        ).format(len(self._duplicates)))
        self._result_current_label.set(
            "Showing: {0} of {1}".format(
                self._duplicate_index + 1, len(self._duplicates)
            )
        )

    def next_duplicate(self):
        """next_duplicate."""
        self._duplicate_index += 1
        self.update_output()

    def prev_duplicate(self):
        """prev_duplicate."""
        self._duplicate_index -= 1
        self.update_output()

    def open_browse_dialog(self):
        """open_browse_dialog."""
        self.set_start_state()
        dirname = askdirectory(initialdir="/")
        self.path.set(dirname)
        self._result_total_var.set('Scan directory for duplicates!')
        self._result_current_label.set('No results yet!')


# Fixme! Legacy variables:
duplicates_gui = DuplicatesApp

if __name__ == '__main__':
    APP = DuplicatesApp() # o_O ???
    APP.master.title("DuplicatesDeletion")
    APP.mainloop()
