#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2012~2013 Deepin, Inc.
#               2012~2013 Long Wei
#
# Author:     Long Wei <yilang2007lw@gmail.com>
# Maintainer: Long Wei <yilang2007lw@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import gtk
from dtk.ui.label import Label
from dtk.ui.combo import ComboBox,ComboBoxItem
from dtk.ui.button import Button,CheckButton
from dtk.ui.listview import ListView
from dtk.ui.frame import HorizontalFrame
from dtk.ui.scrolled_window import ScrolledWindow
from part_list_item import PartListItem
from part_util import global_part_util
from ui_utils import switch_box
from part_new import PartNew
from part_edit import PartEdit
import re

class Part(gtk.VBox):
    '''Part UI'''
    def __init__(self):
        super(Part,self).__init__()

        self.selected_disk=None
        self.selected_disk_partitions=None
        self.selected_part=None
        self.part_util=global_part_util
        self.new_part_path=""

        #select disk box
        choose_disk_box=gtk.HBox()
        choose_disk_label=Label("选择硬盘:    ")
        disk_info=self.part_util.get_install_device_info()
        self.choose_disk_combo=ComboBox()
        for disk in disk_info.keys():
            disk_combo_item=ComboBoxItem(disk,None)
            self.choose_disk_combo.add_item(disk_combo_item)

        self.choose_disk_combo.set_select_index(0)    
        # self.selected_disk=self.part_util.get_disk_from_path("/dev/sda")
        self.choose_disk_combo.connect("item-selected",self.on_disk_combo_selected)
        self.update_selected_disk()
        choose_disk_box.pack_start(choose_disk_label,True,True,4)
        choose_disk_box.pack_start(self.choose_disk_combo,True,True,4)

        #disk partitions button
        self.partition_btns_container_box=gtk.VBox()
        self.selected_part_btn=None
        self.update_part_btn_box()

        #partitions list view
        self.part_listview_container_box=gtk.VBox()
        self.part_listview_items=self.init_part_listview_items()
        self.update_part_listview()

        
        #partition admin buttons
        part_set_box=gtk.HBox(False,12)
        part_set_box.set_size_request(100,30)
        self.part_new_table_btn=Button("新建分区表")
        self.part_new_btn=Button("新建分区")
        self.part_edit_btn=Button("编辑分区")
        self.part_delete_btn=Button("删除分区")
        self.part_recovery_btn=Button("还原分区表")

        self.part_new_table_btn.connect("clicked",self.on_part_new_table_clicked)
        self.part_new_btn.connect("clicked",self.on_part_new_btn_clicked)
        self.part_edit_btn.connect("clicked",self.on_part_edit_btn_clicked)
        self.part_delete_btn.connect("clicked",self.on_part_delete_btn_clicked)
        self.part_recovery_btn.connect("clicked",self.on_part_recovery_btn_clicked)

        self.part_delete_btn.set_clickable(False)
        self.part_edit_btn.set_clickable(False)
        part_set_box.pack_start(self.part_new_table_btn,False,False,4)
        part_set_box.pack_start(self.part_new_btn,False,False,4)
        part_set_box.pack_start(self.part_edit_btn,False,False,4)
        part_set_box.pack_start(self.part_delete_btn,False,False,4)
        part_set_box.pack_start(self.part_recovery_btn,False,False,4)
        
        #pack above boxes
        self.part_frame=HorizontalFrame()
        part_box=gtk.VBox()
        # part_box.set_size_request(400,-1)
        part_box.pack_start(choose_disk_box,False,False,4)
        part_box.pack_start(self.partition_btns_container_box,False,False,4)
        part_box.pack_start(self.part_listview_container_box,False,False,4)
        part_box.pack_start(part_set_box,False,False,4)
        self.part_frame.add(part_box)
        self.part_frame.set_padding(0,0,30,30)
        
        self.add(self.part_frame)


#here comes basic function for update UI data

    def update_selected_disk(self):
        '''changed the current used and displayed disk'''
        self.selected_disk=self.part_util.get_disk_from_path(self.choose_disk_combo.get_current_item().get_label())
        return self.selected_disk

    def update_selected_disk_partitions(self):
        '''update the partitions list of the selected_disk'''
        self.update_selected_disk()
        self.selected_disk_partitions=self.part_util.get_disk_partitions(self.selected_disk)
        return self.selected_disk_partitions
    
    def update_disk_main_list(self):
        '''return main partitions list of the selected_disk'''
        self.update_selected_disk_partitions()
        return filter(lambda item:item.type==0 or item.type==2,self.selected_disk_partitions)

    def update_disk_primary_list(self):
        '''return primary partitions list of the selected_disk'''
        self.update_selected_disk_partitions()
        return filter(lambda item:item.type==0,self.selected_disk_partitions)
        
    def update_disk_logical_list(self):
        '''return logical partitions list of the selected_disk'''
        self.update_selected_disk_partitions()
        return filter(lambda item:item.type==1,self.selected_disk_partitions)

    def update_disk_extend_list(self):
        '''return extend partitions list of the selected_disk'''
        self.update_selected_disk_partitions()
        return filter(lambda item:item.type==2,self.selected_disk_partitions)

    def get_new_add_part_path(self,part_obj):
        '''get new added part path of disk_part_display_path and react to the dict'''
        main_part_list=filter(lambda item :item.type==0 or item.type==2,self.part_util.disk_part_display_path[self.selected_disk].keys())
        extend_part_list=filter(lambda item: item.type==2,self.part_util.disk_part_display_path[self.selected_disk].keys())
        logical_part_list=filter(lambda item :item.type==1,self.part_util.disk_part_display_path[self.selected_disk].keys())

        new_part_path=""
        max_num=0
        if part_obj.type==0:
            if len(main_part_list) > 3:
                print "can at most have 4 primary partition"
            elif len(main_part_list)==0:
                new_part_path=self.selected_disk.device.path+str(1)
            else:
                for part in main_part_list:
                    part_no=int(filter(str.isdigit,self.part_util.disk_part_display_path[self.selected_disk][part])[:])
                    if part_no > max_num:
                        max_num=part_no

                new_part_path=self.selected_disk.device.path+str(int(max_num)+1)

            self.part_util.disk_part_display_path[self.selected_disk][part_obj]=new_part_path
            return self.part_util.disk_part_display_path

        elif part_obj.type==2:
            for part in main_part_list:
                if part.type==2:
                    print "can have only one extend "
            if len(main_part_list) > 3:
                print "can at most have 4 primary partition"
            elif len(main_part_list)==0:
                new_part_path=self.selected_disk.device.path+str(1)
            else:
                for part in main_part_list:
                    part_no=int(filter(str.isdigit,self.part_util.disk_part_display_path[self.selected_disk][part])[:])
                    if part_no > max_num:
                        max_num=part_no

                new_part_path=self.selected_disk.device.path+str(int(max_num)+1)

            self.part_util.disk_part_display_path[self.selected_disk][part_obj]=new_part_path
            return self.part_util.disk_part_display_path

        elif part_obj.type==1:
            if len(extend_part_list)!=1:
                print "must have only one extend part first"
                return self.part_util.disk_part_display_path

            if len(logical_part_list)==0:
                new_part_path=self.selected_disk.device.path+str(5)
            else:
                for part in logical_part_list:
                    part_no=int(filter(str.isdigit,self.part_util.disk_part_display_path[self.selected_disk][part])[:])
                    if part_no > max_num:
                        max_num=part_no

                new_part_path=self.selected_disk.device.path+str(int(max_num)+1)

            self.part_util.disk_part_display_path[self.selected_disk][part_obj]=new_part_path
            return self.part_util.disk_part_display_path

        else:
            print "invalid part type"
            return self.part_util.disk_part_display_path

    def get_delete_part_other_path(self,part_obj):
        '''update the disk_part_display_path when delete a partition'''
        main_part_list=filter(lambda item :item.type==0 or item.type==2,self.part_util.disk_part_display_path[self.selected_disk].keys())
        extend_part_list=filter(lambda item: item.type==2,self.part_util.disk_part_display_path[self.selected_disk].keys())
        logical_part_list=filter(lambda item :item.type==1,self.part_util.disk_part_display_path[self.selected_disk].keys())

        if part_obj not in self.part_util.disk_part_display_path[self.selected_disk].keys():
            print "part_obj not in disk_part_display_path,some error occurs"

        current_num=int(filter(str.isdigit,self.part_util.disk_part_display_path[self.selected_disk][part_obj])[:])    

        if part_obj.type==0:
            if len(main_part_list)==1:
                del self.part_util.disk_part_display_path[self.selected_disk][part_obj]
                return self.part_util.disk_part_display_path
            else:    
                part_prefix=re.findall(r'[^0-9]+',self.part_util.disk_part_display_path[self.selected_disk][part_obj])[0]
                for part in main_part_list:
                    part_no=int(filter(str.isdigit,self.part_util.disk_part_display_path[self.selected_disk][part])[:])
                    if part_no > current_num:
                        self.part_util.disk_part_display_path[self.selected_disk][part]=part_prefix+str(part_no-1)
                del self.part_util.disk_part_display_path[self.selected_disk][part_obj]
                return self.part_util.disk_part_display_path

        elif part_obj.type==2:
            if len(logical_part_list)!=0:
                for part in logical_part_list:
                    del self.part_util.disk_part_display_path[self.selected_disk][part]

            part_prefix=re.findall(r'[^0-9]+',self.part_util.disk_part_display_path[self.selected_disk][part_obj])[0]
            for part in main_part_list:
                part_no=int(filter(str.isdigit,self.part_util.disk_part_display_path[self.selected_disk][part])[:])
                if part_no > current_num:
                    self.part_util.disk_part_display_path[self.selected_disk][part]=part_prefix+str(part_no-1)

            del self.part_util.disk_part_display_path[self.selected_disk][part_obj]
            return self.part_util.disk_part_display_path

        elif part_obj.type==1:
            if len(extend_part_list)!=1:
                print "must have one extend part first"
                return self.part_util.disk_part_display_path
            if len(logical_part_list)==1:
                del self.part_util.disk_part_display_path[self.selected_disk][part_obj]
            else:
                part_prefix=re.findall(r'[^0-9]+',self.part_util.disk_part_display_path[self.selected_disk][part_obj])[0]
                for part in logical_part_list:
                    part_no=int(filter(str.isdigit,self.part_util.disk_part_display_path[self.selected_disk][part])[:])
                    if part_no > current_num:
                        self.part_util.disk_part_display_path[self.selected_disk][part]=part_prefix+str(part_no-1)
                del self.part_util.disk_part_display_path[self.selected_disk][part_obj]
                return self.part_util.disk_part_display_path

        else:
            print "invalid part type"
            return self.part_util.disk_part_display_path


    def update_choose_disk_combo(self):
        '''update the item of choose disk'''
        self.update_selected_disk()

    def update_part_btn_box(self):
        '''when change disk,the partitions display changed'''
        total_width=600
        total_length=self.selected_disk.device.length
        partition_box=gtk.HBox()
        partition_box.set_size_request(-1,35)

        disk_part_itemlist=filter(lambda item:item[0].disk==self.selected_disk and item[0].type==0
                                  or item[0].type==1,self.part_util.disk_partition_info_tab)
        button_part_list=[]
        for item in disk_part_itemlist:
            button_part_list.append(item[0])

        for part in button_part_list:
            part_btn=Button("Button")
            part_btn.set_label(part.path)
            width=total_width*((float)(part.geometry.length)/(float)(total_length))
            if width<10:
                pass
            else:
                hbox=gtk.HBox()
                hbox.set_size_request((int)(width),30)
                hbox.add(part_btn)
            partition_box.pack_start(hbox,True,True,1)
            part_btn.connect("clicked",self.on_part_btn_clicked)    

        switch_box(self.partition_btns_container_box,partition_box)    
        
    def init_part_listview_items(self):
        '''update listview_items,mostly used when change disk or first load'''
        self.update_selected_disk()

        self.disk_partition_info=filter(lambda item:item[0].disk==self.selected_disk,self.part_util.disk_partition_info_tab)
        part_listview_items=[]
        # print "before init part list view items:\n"
        # print part_listview_items
        for item in self.disk_partition_info:
            if item[-1]=="delete":
                pass
            else:
                # part_list_item=PartListItem(self.selected_disk,item[0],str(item[7]),str(item[4]),str(item[5]),"8G",item[2])
                part_list_item=PartListItem(self.selected_disk,item[0],str(item[7]),str(item[4]),str(item[5]),str(item[3]),item[2])
                # part_list_item=PartListItem(str(item[0].path),str(item[4]),str(item[7]),CheckButton(),"8G","4G",item[2])
                part_listview_items.append(part_list_item)

        return part_listview_items
    
    def update_part_listview(self):
        '''reload listview because the listview_items changed,need give self.part_listview_items before called'''
        self.update_selected_disk_partitions()
        part_listview_box=gtk.VBox()
        part_listview_box.set_size_request(-1,280)
        # self.part_listview_items=self.init_part_listview_items()    #because recovery part table don't need this
        self.part_listview=ListView(
            # [(lambda item:item.partition,cmp),
            [(lambda item:item.part_path,cmp),
            (lambda item:item.mp,cmp),
            (lambda item:item.fstype,cmp),
            (lambda item:item.format,cmp),
            (lambda item:item.total_size,cmp),
            (lambda item:item.part_type,cmp)
             ]
            )
        self.part_listview.set_expand_column(1)
        self.part_listview.add_titles(["分区","挂载点","文件系统","格式化","总容量(MB)","类型"])
        if len(self.part_listview_items)==0:
            pass
        else:
            self.part_listview.add_items(self.part_listview_items)
        self.part_listview.connect("single-click-item",self.on_part_item_clicked)
        self.part_listview.connect("double-click-item",self.on_part_item_clicked)
        # self.part_listview.cell_widths=[100,80,100,60,60,60,100]
        self.part_listview.keep_select_status()
        part_scrolled_window=ScrolledWindow()
        part_scrolled_window.add_child(self.part_listview)
        part_listview_box.add(part_scrolled_window)
        part_listview_box.show_all()
        switch_box(self.part_listview_container_box,part_listview_box)

    def add_part_2btn_box(self):
        '''add new added part to part_btn_box'''
        #need do actually add operation first
        self.update_part_btn_box()

    def add_part_2listview(self,part_listview_item):
        '''add new added partition to listview'''
        # need do autually add operation first
        part_listview_items=[]
        # part_listview_item1=PartListItem("/dev/hda1","ext4","/test","True","8G","4G","primary")
        # part_listview_item2=PartListItem("/dev/hda2","ext4","/test","True","8G","4G","primary")
        # part_listview_items.append(part_listview_item1)
        # part_listview_items.append(part_listview_item2)
        part_listview_items.append(part_listview_item)
        self.part_listview.add_items(part_listview_items)

    def delete_part_from_listview(self):
        '''delete part from listview'''
        #need do real delete operation first
        self.part_listview_items=self.init_part_listview_items()
        self.update_part_listview()

    def delete_part_form_btn_box(self):
        '''delete part from btn box'''
        #need do real delete operation first
        self.update_part_btn_box()

    def get_part_from_listview(self):
        '''get partition object from the current_item of the listview'''
        pass

    def get_part_from_btn_box(self):
        '''get partition object form the current_item of btn_box'''
        pass

#below comes directly operations by UI
    def on_disk_combo_selected(self,widget,event):
        '''change disk,react to partitions display'''
        self.selected_disk=self.update_selected_disk()
        self.update_part_btn_box()
        self.part_listview_items=self.init_part_listview_items()
        self.update_part_listview()
    
    def on_part_btn_clicked(self,widget):
        '''react to listview'''
        print "btn clicked"
        self.selected_part_btn=widget
        print widget.label

    def on_part_item_clicked(self,arg1,arg2,arg3,arg4,arg5):
        '''one part clicked'''
        self.current_part_item=self.part_listview.get_current_item()
        if self.current_part_item.partition.type==2:
            self.part_edit_btn.set_clickable(False)
            if len(self.part_util.get_disk_logical_partitions(self.selected_disk))!=0:
                self.part_delete_btn.set_clickable(False)
            else:
                self.part_delete_btn.set_clickable(True)
        else:
            self.part_edit_btn.set_clickable(True)
            self.part_delete_btn.set_clickable(True)

        return self.current_part_item

    def set_part_item_focus(self):
        '''set part_item_focus'''
        pass

    def on_part_new_table_clicked(self,widget):
        '''create new partition table of the selected disk'''
        self.update_part_btn_box()
        self.part_util.rebuild_disk_partition_info_tab(self.selected_disk)

        self.part_listview.clear()

    def on_part_new_btn_clicked(self,widget):
        '''create new partition'''
        #update_part_btn_box and listview after add partition operation
        self.part_new=PartNew(self.on_part_new_ok_btn_clicked,self.selected_disk)
        self.part_new.show_all()

    def on_part_new_ok_btn_clicked(self,widget):
        '''confirm to add new partition'''
        disk_path=self.selected_disk.device.path
        
        part_type=self.part_new.part_type_combo.get_current_item().get_label()
        part_type_dict={"主分区":"primary","扩展分区":"extend","逻辑分区":"logical",
                        "primary":"primary","logical":"logical","extend":"extend"}

        part_type=part_type_dict[part_type]

        part_capacity=self.part_new.part_capacity_spin.get_value()
        part_fs=self.part_new.part_fs_combo.get_current_item().get_label()
        part_format=True
        part_format_str="True"
        part_name=None
        part_location=self.part_new.part_location_combo.get_current_item().get_label()
        part_mp=self.part_new.part_mp_combo.get_current_item().get_label()
        self.part_util.add_disk_partition_info_tab(disk_path,part_type,part_capacity,part_fs,part_format,part_name,part_mp)
        part_obj=self.part_util.to_add_partition

        self.get_new_add_part_path(part_obj)
        # part_path=self.generate_disk_part_path(part_type)
        # self.part_util.disk_part_display_path[self.selected_disk][part_obj]=part_path
        # part_listview_item=PartListItem(part_path,part_fs,part_mp,part_format_str,str(part_capacity),"4G",part_type)
        part_listview_item=PartListItem(self.selected_disk,part_obj,part_mp,part_fs,part_format_str,str(part_capacity),part_type)

        self.add_part_2listview(part_listview_item)
        self.update_selected_disk_partitions()
        self.udpate_part_btn_box()
        # print self.part_util.get_disk_partitions(self.selected_disk)
        # self.add_part_2btn_box()
        # self.update_display_part_path()
        self.part_new.destroy()

    def on_part_edit_btn_clicked(self,widget):
        '''edit selected partition'''
        if self.part_listview.get_current_item()==None:
            print "must selected a partition first!"
            return 
        self.current_part=self.part_listview.get_current_item().partition
        self.part_edit=PartEdit(self.on_part_edit_ok_btn_clicked,self.current_part)
        self.part_edit.show_all()

    def on_part_edit_ok_btn_clicked(self,widget):
        '''confirm to edit partition'''
        #need also alter info in the backend table,
        part_edit_fs=self.part_edit.part_fs_combo.get_current_item().get_label()
        part_edit_mp=self.part_edit.part_mp_combo.get_current_item().get_label()

        for item in self.part_util.disk_partition_info_tab:
            if item[0]==self.current_part:
                if part_edit_fs==item[4]:
                    part_edit_format=False
                else:
                    part_edit_format=True
                    item[4]=part_edit_fs
                item[7]=part_edit_mp
                item[5]=part_edit_format
            else:
                continue
        #then need update listview
        self.part_listview_items=self.init_part_listview_items()        
        self.update_part_listview()
        self.part_edit.destroy()
        self.part_listview.select_to_prev_item()

    def on_part_delete_btn_clicked(self,widget):
        '''delete partition'''
        if self.part_listview.get_current_item()==None:
            print "must select a partition first"
            return
        self.current_part=self.part_listview.get_current_item().partition
        # index=self.part_listview.get_current_item().get_index()
        for item in self.part_util.disk_partition_info_tab:
            if item[0]==self.current_part:
                self.part_util.delete_disk_partition_info_tab(self.current_part)
                self.get_delete_part_other_path(self.current_part)
                self.part_listview_items=self.init_part_listview_items()
                self.update_part_listview()
            else:
                continue
        self.part_listview.select_to_prev_item()
        self.update_part_btn_box()

    def on_part_recovery_btn_clicked(self,widget):
        '''recovery part info to backup,consider frontend and backend'''
        self.update_part_btn_box()
        self.part_util.recovery_disk_partition_info_tab(self.selected_disk)
        self.part_listview.clear()

        # disk_partition_info=filter(lambda item:item[0].disk==self.selected_disk,self.part_util.backup_disk_partition_info_tab)
        # for item in disk_partition_info:
        #     if item[-1]=="delete":
        #         pass
        #     else:
        #         part_list_item=PartListItem(self.selected_disk,item[0],str(item[4]),str(item[7]),str(item[5]),"8G","4G",item[2])
                # self.part_listview_items.append(part_list_item)
        self.part_listview_items=self.init_part_listview_items()
        self.update_part_listview()
        self.update_part_btn_box()