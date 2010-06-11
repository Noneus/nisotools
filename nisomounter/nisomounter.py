#!/usr/bin/env python

import sys
import os
import shutil
from subprocess import Popen, PIPE

#
# Check for the right pygtk version
#
try:
	import pygtk
	pygtk.require("2.0")
except:
	pass

try:
	import gtk
	import gtk.glade
except:
	print "You need to install pyGTK or GTKv2 ",
	print "or set your PYTHONPATH correctly."
	sys.exit(1)

#
# the main app
#
class nisomounter:
	basePath = "/media"
	confPath = os.path.join(os.path.expanduser("~"), ".config/nisotools")
	
	def __init__(self):
		# we need to be root
		if os.getuid() != 0:
			cmd = "gksudo python \"%s\"" % "\" \"".join(sys.argv)
			sys.exit(os.system(cmd))
		
		# where is the glade file?
		gladeName = 'nisomounter.glade'
		if os.path.exists(gladeName):
			gladePath = gladeName
		else:
			from pkg_resources import Requirement, resource_filename
			gladePath = resource_filename(Requirement.parse("nisotools"), "share/nisotools/glade/nisomounter.glade")
			if not os.path.exists(gladePath):
				gladePath = os.path.join(sys.prefix, "share/nisotools/glade", gladeName)
		
		
		# The callbacks
		callbacks = {
			"on_mainwindow_destroy": gtk.main_quit,
			"mount_iso": self.mountiso,
			"unmount_iso": self.unmountiso,
			"exit": self.exit
		}
		
		# Initialize the interface
		self.wTree=gtk.glade.XML(gladePath, "mainwindow")
		self.wTree.signal_autoconnect(callbacks)
		
		# set treemodel
		self.mountTree = self.wTree.get_widget("mountlist")
		self.mountlist = gtk.ListStore(str, str)
		self.mountTree.set_model(self.mountlist)
		
		# create the two columns
		column = gtk.TreeViewColumn("ISO-Path", gtk.CellRendererText(), text=0)
		column.set_resizable(True)
		column.set_sort_column_id(0)
		self.mountTree.append_column(column)
		column = gtk.TreeViewColumn("Mount-Path", gtk.CellRendererText(), text=1)
		column.set_resizable(True)
		column.set_sort_column_id(1)
		self.mountTree.append_column(column)
		
		# fill the columns with data
		self.refreshmounts()
		
		return
	
	# fills the treeview with data
	def refreshmounts(self):
		# mounted isos use iso9660 as filesystem and are mounted with loop
		output = os.popen("mount | grep 'type iso9660' | grep '/dev/loop'").read()
		
		# first empty the treeview
		self.mountlist.clear()
		
		# fill the list
		for line in output.split("\n"):
			if line:
				buff = line.split(" on ")
				isoPath = buff[0]
				mountPath = buff[1].split(" type ")[0]
				self.mountlist.append([isoPath, mountPath])
	
	def unmountiso(self, widget):
		# unmount only if something is selected
		try:
			model, row = self.mountTree.get_selection().get_selected()
			mountPath = model[row][1]
		except:
			return
		
		# unmount the iso
		umountCmd = "umount \"%s\"" % mountPath
		if os.system(umountCmd) != 0:
			self.errormsg("Couldn't unmount ISO!")
			return
		
		# we no longer need the mountpoint
		shutil.rmtree(mountPath)
		
		self.refreshmounts()
	
	def mountiso(self, widget):
		# check if an iso file was chosen
		isoPath = self.wTree.get_widget("isochooser").get_filenames()[0]
		if not isoPath.endswith(".iso"):
			self.errormsg("Couldn't mount ISO: '%s' not an ISO." % isoPath)
			return
		
		# create the mountpoint
		isoName = os.path.basename(isoPath).replace(".iso", "")
		mountPath = os.path.join(self.basePath, isoName)
		os.makedirs(mountPath)
		
		# mount the iso
		mountCmd = "mount -o loop,user -t iso9660 \"%s\" \"%s\"" \
			% (isoPath, mountPath)
		mountProc = Popen(mountCmd, shell=True, stdout=PIPE, stderr=PIPE)
		mountProc.wait()
		
		# on error display a dialog
		if mountProc.poll() != 0:
			self.errormsg("Couldn't mount ISO: mount command failed:\n'%s'\nstdout:\n%s\n\nstderr:\n%s" \
				% (mountCmd, mountProc.stdout.read(), mountProc.stderr.read())
			)
			shutil.rmtree(mountPath)
		
		self.refreshmounts()
	
	def errormsg(self, message):
		dialog = gtk.Dialog("ERROR", self.wTree.get_widget("mainwindow"))
		
		label = gtk.Label("ERROR: %s" % message)
		dialog.vbox.pack_start(label, True, True, 0)
		label.show()
		
		button = gtk.Button(stock=gtk.STOCK_CLOSE)
		dialog.vbox.pack_start(button, True, True, 0)
		button.connect_object("clicked", gtk.Widget.destroy, dialog)
		button.show()
		
		dialog.show()
	
	def exit(self, nothing):
		self.wTree.get_widget("mainwindow").destroy()

def main():
	app=nisomounter()
	gtk.main()

if __name__ == "__main__":
    main()

