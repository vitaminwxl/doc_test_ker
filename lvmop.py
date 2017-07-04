#coding:utf-8
import lvm2py as lvm
import os
import sys

class lvmop:
	def __init__(self):
		self.lvm=lvm.LVM()
	def is_exsit_vg(self,vg_name):
		vg=self.lvm.vgscan()
		for i in vg:
			if i.name==vg_name:
				return True
			else:
				return False
	def create_vg(self,vg_name,disklist):
		vg=self.lvm.create_vg(vg_name,disklist)
		return vg
	def is_exsit_lv(self,vg_name,lv_name):
		vg=self.lvm.get_vg(vg_name,"w")
		for i in vg.lvscan():
			if i.name==lv_name:
				return True
		return False
	
	def remove_lv(self,vg_name,lv_name):
		vg=self.lvm.get_vg(vg_name,"w")
		for i in vg.lvscan():
			if i.name==lv_name:
				res=vg.remove_lv(i)
	def create_lv(self,vg_name,lv_name,lv_size,size_unit="GiB"):
		vg=self.lvm.get_vg(vg_name,"w")
		lv=vg.create_lv(lv_name,lv_size,size_unit)
		return lv

def main(lv_type,lv_name,lv_size):
	vg_name='cloud_{0}'.format(lv_type)
	lvm=lvmop()

	#如果卷组不存在则创建
	if not lvm.is_exsit_vg(vg_name):
		lvm.create_vg(vg_name,["/dev/{0}"].format(lv_type))
	#创建lv
	if lvm.is_exsit_lv(vg_name,lv_name):
		print("lv:{0} is exsit".format(lv_name))
		exit(1)
	lv=lvm.create_lv(vg_name,lv_name,lv_size)
	lv_point="/dev/{0}/{1}".format(vg_name,lv_name)
	#格式化lv
	mkfs_res=os.system("mkfs.xfs -q {0}".format(lv_point))	
	if mkfs_res!=0:
		print("mkfs error")
		exit(1)
	#挂载目录
	mount_point="/docker_data/{0}/{1}".format(vg_name,lv_name)
	mkdir_res=os.system("mkdir -p {0}".format(mount_point))
	if mkdir_res!=0:
		print("mkdir error")
		exit(1)
	mount_res=os.system("mount {0} {1}".format(lv_point,mount_point))
	if mount_res!=0:
		print("mount error")
		exit(1)
	print("success")
	
		

if __name__=="__main__":
	if len(sys.argv)!=4:
		print("The number of parameters does not match")
		exit(1)
	#main(sys.argv[1],sys.argv[2],int(sys.argv[3]))
	main(sys.argv[1],sys.argv[2],int(sys.argv[3]))
