#
# ==============================
# Copyright 2011 Whamcloud, Inc.
# ==============================
# REST API Conrtoller for Lustre File systems resource monitor name space
from django.core.management import setup_environ

# Hydra server imports
import settings
setup_environ(settings)

from requesthandler import (AnonymousRequestHandler,
                            extract_request_args,
                            extract_exception)
from monitor.models import (Filesystem,
                            MetadataTarget,
                            ManagementTarget,
                            ObjectStoreTarget,
                            Client,
                            Host,
                            TargetMount)

class ListFileSystems(AnonymousRequestHandler):

    def __init__(self,*args,**kwargs):
        AnonymousRequestHandler.__init__(self,self.list_filesystems)

    @classmethod
    @extract_exception
    def list_filesystems(self,request):
        no_of_ost=0
        no_of_oss=0
        oss_name=''
        mgs_name=''
        mgs_status=''
        mgt_name=''
        mgt_status=''
        mgt_block_device=''
        mgt_mount_point=''
              
        mds_name=''   
        mds_status=''
        mdt_name=''
        mdt_status=''  
        mdt_block_device=''
        mdt_mount_point=''

        all_fs = []
        dashboard_data = Dashboard()
        for fs in dashboard_data.filesystems:
            for fstarget in fs.targets:
                if fstarget.item.role() == 'MGS':
                    for fstarget_mount in fstarget.target_mounts:
                        mgs_name = fstarget_mount.item.host.pretty_name()
                        mgs_status = fstarget.status()
                        mgt_name = fstarget.item.name
                        mgt_block_device = str(fstarget_mount.item.block_device)
                        mgt_mount_point = str(fstarget_mount.item.mount_point)
                if fstarget.item.role() == 'MDT':
                    for fstarget_mount in fstarget.target_mounts:
                        mds_name = fstarget_mount.item.host.pretty_name()
                        mds_status= fstarget_mount.status()
                        mdt_name = fstarget.item.name
                        mdt_status = fstarget.status()
                        mdt_block_device = str(fstarget_mount.item.block_device)
                        mdt_mount_point = str(fstarget_mount.item.mount_point)
                if fstarget.item.role() == 'OST':
                    for fstarget_mount in fstarget.target_mounts:
                        if oss_name != fstarget_mount.item.host.pretty_name():
                            no_of_oss = no_of_oss + 1
                        no_of_ost = no_of_ost + 1
                        oss_name = fstarget_mount.item.host.pretty_name()
            filesystem = Filesystem.objects.get(name=fs.item.name) 
            inodedata = filesystem.metrics.fetch_last(MetadataTarget,fetch_metrics="filesfree filestotal".split())
            diskdata = filesystem.metrics.fetch_last(ObjectStoreTarget,fetch_metrics="kbytesfree kbytestotal".split())
            all_fs.append(
                          {   
                           'fsname': fs.item.name,
                           'mgsname': mgs_name,
                           'mgsstatus':mgs_status,
                           'mgtname': mgt_name,
                           'mgtstatus' :mgt_status,
                           'mgtblockdevice': mgt_block_device,
                           'mgtmountpoint': mgt_mount_point ,          
                           'mdsname':mds_name ,
                           'mdsstatus':mds_status, 
                           'mdtname':mdt_name,
                           'mdtstatus':mdt_status,    
                           'mdtblockdevice':mdt_block_device,
                           'mdt_mount_point':mdt_mount_point, 
                           'noofoss':no_of_oss,
                           'noofost':no_of_ost,
                           'kbytesused':diskdata[1]['kbytestotal'] if diskdata[1]['kbytestotal'] else 0,
                           'kbytesfree':diskdata[1]['kbytesfree'] if diskdata[1]['kbytesfree'] else 0,
                           'mdtfilesfree':inodedata[1]['filesfree'] if inodedata[1]['filesfree'] else 0,
                           'mdtfileused':inodedata[1]['filestotal'] if inodedata[1]['filestotal'] else 0,    
                           'status' : fs.status()
                          } 
                         )
            no_of_ost=0
            no_of_oss=0
            oss_name=''
        return all_fs

class GetFileSystem(AnonymousRequestHandler):

    def __init__(self,*args,**kwargs):
        AnonymousRequestHandler.__init__(self,self.get_filesystem)

    @classmethod
    @extract_request_args(filesystem_name='filesystem')
    @extract_exception
    def get_filesystem(self,request,filesystem_name):
        no_of_ost=0
        no_of_oss=0
        oss_name=''
        mgs_name=''
        mgs_status=''
        mgt_name=''
        mgt_status=''
        mgt_block_device=''
        mgt_mount_point=''
           
        mds_name=''   
        mds_status=''
        mdt_name=''
        mdt_status=''  
        mdt_block_device=''
        mdt_mount_point=''
        #mdt_kbytesfree=0
        #mdt_kbytesused=0
        mdt_filesfree=0
        mdt_filesused=0
        ost_kbytesfree=0
        ost_kbytesused=0                     
        all_fs = []
        dashboard_data = Dashboard()
        for fs in dashboard_data.filesystems:
            if str(fs.item.name) == str(filesystem_name): 
                for fstarget in fs.targets:
                    if fstarget.item.role() == 'MGS':
                        for fstarget_mount in fstarget.target_mounts:
                            mgs_name = fstarget_mount.item.host.pretty_name()
                            mgs_status = fstarget.status()
                            mgt_name = fstarget.item.name
                            mgt_block_device = str(fstarget_mount.item.block_device)
                            mgt_mount_point = str(fstarget_mount.item.mount_point)
                    if fstarget.item.role() == 'MDT':
                        for fstarget_mount in fstarget.target_mounts:
                            mds_name = fstarget_mount.item.host.pretty_name()
                            mds_status= fstarget_mount.status()
                            mdt_name = fstarget.item.name
                            mdt_status = fstarget.status()
                            mdt_block_device = str(fstarget_mount.item.block_device)
                            mdt_mount_point = str(fstarget_mount.item.mount_point)
                            #mdt_kbytesfree = 0
                            #mdt_kbytesused = 0
                            mdt_filesfree = 0
                            mdt_filesused = 0
                    if fstarget.item.role() == 'OST':
                        for fstarget_mount in fstarget.target_mounts:
                            if oss_name != fstarget_mount.item.host.pretty_name():
                                no_of_oss = no_of_oss + 1
                        no_of_ost = no_of_ost + 1
                        oss_name = fstarget_mount.item.host.pretty_name()
                all_fs.append(
                              {   
                               'fsname': fs.item.name,
                               'mgsname': mgs_name,
                               'mgsstatus':mgs_status,
                               'mgtname': mgt_name,
                               'mgtstatus' :mgt_status,
                               'mgtblockdevice': mgt_block_device,
                               'mgtmountpoint': mgt_mount_point ,          
                               'mdsname':mds_name ,
                               'mdsstatus':mds_status, 
                               'mdtname':mdt_name,
                               'mdtstatus':mdt_status,    
                               'mdtblockdevice':mdt_block_device,
                               'mdt_mount_point':mdt_mount_point, 
                               'noofoss':no_of_oss,
                               'noofost':no_of_ost,
                               'kbytesused':ost_kbytesused,
                               'kbytesfree':ost_kbytesfree,
                               'mdtfilesfree':mdt_filesfree,
                               'mdtfileused':mdt_filesused,    
                               'status' : fs.status()
                              } 
                             )
            no_of_ost=0
            no_of_oss=0
            oss_name=''
        return all_fs            

class GetFSVolumeDetails(AnonymousRequestHandler):

    def __init__(self,*args,**kwargs):
        AnonymousRequestHandler.__init__(self,self.get_fs_vol_details)

    @classmethod
    @extract_request_args(filesystem_name='filesystem')
    @extract_exception
    def get_fs_vol_details(self,request,filesystem_name):
        all_fs = []
        dashboard_data = Dashboard()
        for fs in dashboard_data.filesystems:
            if (str(fs.item.name) == str(filesystem_name)) | (not filesystem_name): 
                for fstarget in fs.targets:
                    for fstarget_mount in fstarget.target_mounts:
                        for fstarget_mount in fstarget.target_mounts:
                            all_fs.append(
                                          {
                                           'fsname':fs.item.name,  
                                           'targetid':fstarget.item.id,
                                           'targetname': fstarget.item.name,
                                           'targetdevice': str(fstarget_mount.item.block_device),
                                           'targetmount':str(fstarget_mount.item.mount_point),
                                           'targetstatus':fstarget.status(),
                                           'targetkind': fstarget.item.role(),
                                           'hostname':fstarget_mount.item.host.pretty_name(),
                                           'failover':''
                                          }
                                         )
        return all_fs            

class GetVolumes(AnonymousRequestHandler):

    def __init__(self,*args,**kwargs):
       AnonymousRequestHandler.__init__(self,self.get_volumes)

    @classmethod
    @extract_request_args(filesystem_name='filesystem')
    def get_volumes(self,request,filesystem_name):
        if filesystem_name:
            return self.get_volumes_per_fs(Filesystem.objects.get(name = filesystem_name))
        else:
            volumes_list = []
            for fs in Filesystem.objects.all():
                volumes_list.extend(self.get_volumes_per_fs(fs.name))
        return volumes_list
    
    @classmethod
    def get_volumes_per_fs (self,filesystem_name):
        volume_list = []
        filesystem = Filesystem.objects.get(name = filesystem_name)
        volume_list.append(
                           {
                            'id' : filesystem.id,
                            'name': filesystem.name,
                            'targetpath': '',
                            'targetname':'', 
                            'failover':'',
                            'kind': 'FS', #filesystem.role(),
                            'status' : filesystem.status_string()
                            }
                           )
        try:
            volume_list.append(
                                {
                                 'id' : filesystem.mgs.id,
                                 'name': filesystem.mgs.name,
                                 'targetpath' : '',
                                 'targetname':'',
                                 'failover':'',     
                                 'kind': filesystem.mgs.role(),
                                 'status' : filesystem.mgs.status_string()
                                }
                )
        except ManagementTarget.DoesNotExist:
            pass
        try:
            mdt = MetadataTarget.objects.get (filesystem = filesystem)
            volume_list.append(
                                   {
                                    'id' : mdt.id,
                                    'name': mdt.name,
                                    'targetpath': '',
                                    'targetname':'',
                                    'failover':'',  
                                    'kind': mdt.role(),
                                    'status' : mdt.status_string()
                                   }
                )            
        except MetadataTarget.DoesNotExist:
            pass
        osts = ObjectStoreTarget.objects.filter(filesystem = filesystem)
        volume_list.extend([
                            {
                             'id' : ost.id,
                             'name': ost.name,
                             'targetpath': '',
                             'targetname':'',
                             'failover':'',
                             'kind': ost.role(),
                             'status' : ost.status_string()
                            }  
                            for ost in osts
                           ])
        return volume_list

class GetClients (AnonymousRequestHandler):
         
    def __init__(self,*args,**kwargs):
        AnonymousRequestHandler.__init__(self,self.get_clients)

    @classmethod
    @extract_request_args(filesystem_name='filesystem')
    @extract_exception
    def get_clients(self,request,filesystem_name):
        if filesystem_name :
            return self.__get_clients(filesystem_name)
        else:
            client_list = []
            for filesystem in Filesystem.objects.all():
                client_list.extend(self.__get_clients(filesystem.name))
        return client_list
    
    @classmethod 
    @extract_exception
    def __get_clients(self,filesystem_name):
        fsname = Filesystem.objects.get(name = filesystem_name)
        return [
                { 
                 'id' : client.id,
                 'host' : client.host.address,
                 'mount_point' : client.mount_point,
                  #'status' : self.__mountable_audit_status(client)
                }         
                for client in Client.objects.filter(filesystem = fsname)
        ]

class GetServers (AnonymousRequestHandler):

    def __init__(self,*args,**kwargs):
        AnonymousRequestHandler.__init__(self,self.list_servers)

    @classmethod
    @extract_request_args(filesystem_name='filesystem')
    @extract_exception
    def list_servers(self,request,filesystem_name):
        if filesystem_name:
            fs = Filesystem.objects.get(name=filesystem_name)
            return [
                    { 
                     'id' : host.id,
                     'host_address' : host.address,
                     'failnode':'',
                     'kind' : host.role() ,
                     'lnet_status' : str(host.managedhost.state),
                     'status':host.status_string()
                    }
                    for host in fs.get_servers()
            ]
        else:
            return [
                    {
                     'id' : host.id,
                     'host_address' : host.address,
                     'failnode':'',
                     'kind' : host.role() ,
                     'lnet_status': str(host.managedhost.state),
                     'status':host.status_string()  
                    }
                    for host in Host.objects.all()
            ]


class GetEventsByFilter(AnonymousRequestHandler):

    def __init__(self,*args,**kwargs):
        AnonymousRequestHandler.__init__(self,self.get_events_by_filter)

    @classmethod
    @extract_request_args(host_name='hostname',severity_type='severity',event_type='eventtype',scroll_size='scrollsize',scroll_id='scrollid')
    @extract_exception
    def get_events_by_filter(self,request,host_name,severity_type,event_type,scroll_size,scroll_id):
        from monitor.models import Event
        filter_args = []
        filter_kwargs = {}
        if event_type :
            from django.db.models import Q
            event_type = event_type.lower
            filter_args.append(~Q(**{event_type:None}))
        event_set = Event.objects.filter(*filter_args, **filter_kwargs).order_by('-created_at')  
        return [
                {
                 'event_created_at': event.created_at,
                 'event_host': event.host.pretty_name(),
                 'event_severity':str(event.severity_class()),
                 'event_message': event.message(), 
                }
                for event in event_set
        ]

class GetLatestEvents(AnonymousRequestHandler):

    def __init__(self,*args,**kwargs):
        AnonymousRequestHandler.__init__(self,self.get_latest_events)
    
    @classmethod
    @extract_exception
    def get_latest_events(self,request):
        from monitor.models import Event
        return [
                {
                 'event_created_at': event.created_at,
                 'event_host': event.host.pretty_name() if event.host else '',
                 'event_severity':str(event.severity_class()), # Still need to figure out wheather to pass enum or display string
                 'event_message': event.message(),
                }
                for event in Event.objects.all().order_by('-created_at')
        ]


class GetAlerts(AnonymousRequestHandler):

    def __init__(self,*args,**kwargs):
        AnonymousRequestHandler.__init__(self,self.get_alerts)

    @classmethod
    @extract_request_args(active_flag='active')
    @extract_exception  
    def get_alerts(self,request,active_flag):
        from monitor.models import AlertState
        return [a.to_dict() for a in AlertState.objects.filter(active = active_flag).order_by('end')]

class GetJobs(AnonymousRequestHandler):

    def __init__(self,*args,**kwargs):
        AnonymousRequestHandler.__init__(self,self.get_jobs)

    @classmethod
    @extract_exception
    def get_jobs(self,request):
        from configure.models import Job
        from datetime import timedelta, datetime
        from django.db.models import Q
        # Only retive Job logs for past 60 minutes.
        # This need to fixed to get jobs for any time delta
        # Need input from PM    
        jobs = Job.objects.filter(~Q(state = 'complete') | Q(created_at__gte=datetime.now() - timedelta(minutes=60)))
        return [
                {
                 'id': job.id,
                 'state': job.state,
                 'errored': job.errored,
                 'cancelled': job.cancelled,
                 'created_at': "%s" % job.created_at,
                 'description': job.description(),
                }
                for job in jobs
        ]


class GetLogs(AnonymousRequestHandler):

    def __init__(self,*args,**kwargs):
        AnonymousRequestHandler.__init__(self,self.get_logs)

    @classmethod
    @extract_request_args(display_month='month',display_day='day',only_lustre='lustre')
    @extract_exception
    def get_logs(self,request,display_month,display_day,only_lustre):
        import datetime
        from monitor.models import Systemevents
        display_month = int(display_month)
        display_day = int(display_day) 
        if display_month == 0:
            start_date = datetime.datetime(1970, 1, 1)
        else:
            start_date = datetime.datetime(datetime.datetime.now().year,
                                           display_month, display_day)
        log_data = []
        log_data = Systemevents.objects.filter(devicereportedtime__gt =
                                               start_date).order_by('-devicereportedtime')
        if only_lustre:
            log_data = log_data.filter(message__startswith=" Lustre")
    
        return[
               { 
                'message': log_entry.message,
                'service': log_entry.syslogtag,
                'date': log_entry.devicereportedtime.strftime("%b %d %H:%M:%S"),
                'host': log_entry.fromhost,
               }
               for log_entry in log_data
        ]


def gettimeslice(sample_size=10,interval=5):
    from datetime import timedelta,datetime
    current_time = datetime.now()
    data_slice = []
    for i in xrange(sample_size):
        current_time  = current_time - timedelta(seconds=interval)
        strtime  = current_time.isoformat().split('T')[1]
        data_slice.append(strtime.split('.')[0])
    return data_slice


class Dashboard:
    class StatusItem:
        def __init__(self, dashboard, item):
            self.dashboard = dashboard
            self.item = item

        def status(self):
            return self.dashboard.all_statuses[self.item]
    
    def __init__(self):
        self.all_statuses = {}
        # 1 query for getting all targetmoun
        for mount in TargetMount.objects.all():
            # 1 query per targetmount to get any alerts
            self.all_statuses[mount] = mount.status_string()
        from collections import defaultdict
        target_mounts_by_target = defaultdict(list)
        target_mounts_by_host = defaultdict(list)
        target_params_by_target = defaultdict(list)
        for target_klass in ManagementTarget, MetadataTarget, ObjectStoreTarget:
            # 1 query to get all targets of a type
            for target in target_klass.objects.all():
                # 1 query per target to get the targetmounts
                target_mounts = target.targetmount_set.all()
                try:
                    target_mountable_statuses = dict(
                            [(m, self.all_statuses[m]) for m in target_mounts])
                except KeyError:
                    continue
                target_mounts_by_target[target].extend(target_mounts)
                for tm in target_mounts:
                    target_mounts_by_host[tm.host_id].append(tm)
                self.all_statuses[target] = target.status_string(target_mountable_statuses)

                target_params_by_target[target] = target.get_params()
        self.filesystems = []
        # 1 query to get all filesystems
        for filesystem in Filesystem.objects.all().order_by('name'):
            # 3 queries to get targets (of each type)
            targets = filesystem.get_targets()
            try:
                fs_target_statuses = dict(
                        [(t, self.all_statuses[t]) for t in targets])
            except KeyError:
                continue
            self.all_statuses[filesystem] = filesystem.status_string(fs_target_statuses)
            fs_status_item = Dashboard.StatusItem(self, filesystem)
            fs_status_item.targets = []
            for target in targets:
                target_status_item = Dashboard.StatusItem(self, target)
                target_status_item.target_mounts = []
                for tm in target_mounts_by_target[target]:
                    target_mount_status_item = Dashboard.StatusItem(self, tm)
                    target_mount_status_item.target_params = target_params_by_target[target]
                    target_status_item.target_mounts.append(target_mount_status_item)
                fs_status_item.targets.append(target_status_item)

            self.filesystems.append(fs_status_item)

        self.hosts = []
        # 1 query to get all hosts
        for host in Host.objects.all().order_by('address'):
            host_tms = target_mounts_by_host[host.id]
            # 1 query to get alerts
            host_tm_statuses = dict([(tm, self.all_statuses[tm]) for tm in host_tms])
            self.all_statuses[host] = host.status_string(host_tm_statuses)
            host_status_item = Dashboard.StatusItem(self, host)
            host_status_item.target_mounts = [Dashboard.StatusItem(self, tm) for tm in host_tms]




#TODO:
#     This chart data API call is a place holder for r3d layer interface data fetch
#     Currently i am passing the cooked up data using random function till we get
#     actual data from the r3d layer
#     API interface and chart data format will ramain same
class GetFSDiskUsage(AnonymousRequestHandler):

    def __init__(self,*args,**kwargs):
        AnonymousRequestHandler.__init__(self,self.get_fs_diskusage)

    @classmethod
    @extract_request_args(filesystem_name='filesystem',start_time='starttime',end_time='endtime' ,data_function='datafunction')
    @extract_exception
    def get_fs_diskusage(self,request,filesystem_name,start_time,end_time ,data_function):
            from random import uniform
        #try:
            if filesystem_name :
                return [ 
                        {
                         'timestamp' : '1316847600',
                         'filesystem' : filesystem_name,
                         'kbytesfree' : uniform(0,4940388537.9860001),
                         'kbytestotal': '4940834834.4740801',
                        }
                       ]
            else :
                return [
                        {
                         'timestamp' : '1316847600',
                         'filesystem' : filesystem.name,
                         'kbytesfree' : uniform(0,4940388537.9860001),
                         'kbytestotal': '4940834834.4740801',
                        }
                        for filesystem in Filesystem.objects.all() 
                ]      
        #except:
        #    raise  Exception('POST call API_Exception:get_fs_diskusage(filesystem_name,start_time,end_time ,data_function) => Failed to get data for inputs filesystem=%s|starttime=%s|endtime%s |datafunction=%s' %filesystem_name %start_time %end_time   %data_function)

#TODO:
#     This chart data API call is a place holder for r3d layer interface data fetch
#     Currently i am passing the cooked up data using random function till we get
#     actual data from the r3d layer
#     API interface and chart data format will ramain same
class GetFSInodesUsage(AnonymousRequestHandler):

    def __init__(self,*args,**kwargs):
        AnonymousRequestHandler.__init__(self,self.get_fs_indoesusage)

    @classmethod
    @extract_request_args(filesystem_name='filesystem',start_time='starttime',end_time='endtime' ,data_function='datafunction')
    @extract_exception
    def get_fs_indoesusage(self,request,filesystem_name,start_time,end_time ,data_function):
            from random import randrange
        #try:
            if filesystem_name :
              return [
                        {
                         'timestamp' : '1316847600',
                         'filesystem' : filesystem_name,
                         'filesfree' : randrange(0,4940388537,3),
                         'filestotal': '4940834834',
                        }
                       ]
            else :
                return [
                        {
                         'timestamp' : '1316847600',
                         'filesystem' : filesystem.name,
                         'filesfree' : randrange(0,4940388537,3),
                         'filestotal': '4940834834',
                        }
                        for filesystem in Filesystem.objects.all()
                ]
        #except:
        #    raise  Exception('POST call API_Exception:get_fs_inodesusage(filesystem_name,start_time,end_time ,data_function) => Failed to get data for inputs filesystem=%s|starttime=%s|endtime%s |datafunction=%s' %filesystem_name %start_time %end_time   %data_function)

#TODO:
#     This chart data API call is a place holder for r3d layer interface data fetch
#     Currently i am passing the cooked up data using random function till we get
#     actual data from the r3d layer
#     API interface and chart data format will ramain same
class GetServerCPUUsage(AnonymousRequestHandler):

    def __init__(self,*args,**kwargs):
        AnonymousRequestHandler.__init__(self,self.get_server_cpuusage)

    @classmethod
    @extract_request_args(host_name='hostname',start_time='starttime',end_time='endtime' ,data_function='datafunction')
    @extract_exception
    def get_server_cpuusage(self,request,host_name,start_time,end_time ,data_function):
        #try:
            from  random import randrange
            data_slice = [] 
            current_slice = gettimeslice()
            if host_name :
                for slice in current_slice:
                    data_slice.append(    
                                      {
                                       'timestamp': slice,
                                       'hostname' : host_name,
                                       'cpu' : randrange(0,100,3),
                                      }
                                     ) 
                return data_slice    
            else :
                for host in Host.objects.all():
                    for slice in current_slice:
                        data_slice.append(
                                          {
                                           'timestamp': slice,
                                           'hostname' : host.address,
                                           'cpu' : randrange(0,100,3),
                                          }
                                         )
                return data_slice                       
        #except:
        #    raise Exception('POST call API_Exception:get_server_cpuusage(host_name,start_time,end_time ,data_function) => Failed to get data for inputs hostname=%s|starttime=%s|endtime%s |datafunction=%s' %host_name %start_time %end_time   %data_function)

#TODO:
#     This chart data API call is a place holder for r3d layer interface data fetch
#     Currently i am passing the cooked up data using random function till we get
#     actual data from the r3d layer
#     API interface and chart data format will ramain same
class GetServerMemoryUsage(AnonymousRequestHandler):

    def __init__(self,*args,**kwargs):
        AnonymousRequestHandler.__init__(self,self.get_server_memoryusage)

    @classmethod
    @extract_request_args(host_name='hostname',start_time='starttime',end_time='endtime' ,data_function='datafunction')
    @extract_exception
    def get_server_memoryusage(self,request,host_name,start_time,end_time ,data_function):
        #try:
            from  random import randrange
            data_slice = []
            current_slice = gettimeslice()
            if host_name :
                for slice in current_slice:
                    data_slice.append(
                                      {
                                       'timestamp': slice,
                                       'hostname' : host_name,
                                       'memory' : randrange(1024,16384,3),
                                      }
                                     )
                return data_slice
            else :
                for host in Host.objects.all():
                    for slice in current_slice:
                        data_slice.append(
                                          {
                                           'timestamp': slice,
                                           'hostname' : host.address,
                                           'memory' : randrange(1024,16384,3),
                                          }
                                         )
                return data_slice
        #except:
        #    raise  Exception('POST call API_Exception:get_server_memoryusage(host_name,start_time,end_time ,data_function) => Failed to get data for inputs hostname=%s|starttime=%s|endtime%s |datafunction=%s' %host_name %start_time %end_time   %data_function)

#TODO:
#     This chart data API call is a place holder for r3d layer interface data fetch
#     Currently i am passing the cooked up data using random function till we get
#     actual data from the r3d layer
#     API interface and chart data format will ramain same
class GetTargetReads(AnonymousRequestHandler):

    def __init__(self,*args,**kwargs):
        AnonymousRequestHandler.__init__(self,self.get_target_reads)

    @classmethod
    @extract_request_args(target_name='targetname',start_time='starttime',end_time='endtime' ,data_function='datafunction')
    @extract_exception
    def get_target_reads(self,request,target_name,start_time,end_time ,data_function):
        #try:
            from random import randrange
            data_slice = []
            current_slice = gettimeslice()
            if target_name :
                for slice in current_slice:
                    data_slice.append(    
                                      {
                                       'timestamp' : slice,
                                       'targetname' : target_name,
                                       'reads' : randrange(1024,16384,3),
                                      }
                                     )
                return data_slice 
            else :
                 volume_list = []
                 for fs in Filesystem.objects.all():
                    try:
                        for slice in current_slice:
                            data_slice.append(
                                              {
                                               'timestamp' : slice,
                                               'targetname' : fs.mgs.name,
                                               'reads' : randrange(1024,16384,3),
                                              }
                                             )
                    except ManagementTarget.DoesNotExist:
                        pass
                    try:
                        mdt = MetadataTarget.objects.get(filesystem = fs)
                        volume_list.append(
                                           {
                                            'timestamp' : slice,
                                            'targetname' : mdt.name,
                                            'reads' : randrange(1024,16384,3),
                                           }
                                          )
                    except MetadataTarget.DoesNotExist:
                        pass
                    try:
                        osts = ObjectStoreTarget.objects.filter(filesystem = fs)
                        for ost in osts:
                            for slice in current_slice:  
                                data_slice.append(
                                                  {
                                                   'timestamp' :slice,
                                                   'targetname' : ost.name,
                                                   'reads' : randrange(1024,16384,3),
                                                  }
                                                 )
                    except:
                        pass 
                    return data_slice
        #except:
        #    raise  Exception('POST call API_Exception:get_target_reads(target_name,start_time,end_time ,data_function) => Failed to get data for inputs targetname=%s|starttime=%s|endtime%s |datafunction=%s' %target_name %start_time %end_time   %data_function)

#TODO:
#     This chart data API call is a place holder for r3d layer interface data fetch
#     Currently i am passing the cooked up data using random function till we get
#     actual data from the r3d layer
#     API interface and chart data format will ramain same
class GetTargetWrites(AnonymousRequestHandler):

    def __init__(self,*args,**kwargs):
        AnonymousRequestHandler.__init__(self,self.get_target_writes)

    @classmethod
    @extract_request_args(target_name='targetname',start_time='starttime',end_time='endtime' ,data_function='datafunction')
    @extract_exception
    def get_target_writes(self,request,target_name,start_time,end_time ,data_function):
        #try:
            from random import randrange
            data_slice = []
            current_slice = gettimeslice()
            if target_name :
                for slice in current_slice:
                    data_slice.append(
                                      {
                                       'timestamp' : slice,
                                       'targetname' : target_name,
                                       'writes' : randrange(1024,16384,3),
                                      }
                                     )
                return data_slice
            else :
                 volume_list = []
                 for fs in Filesystem.objects.all():
                    try:
                        for slice in current_slice:
                            data_slice.append(
                                              {
                                               'timestamp' : slice,
                                               'targetname' : fs.mgs.name,
                                               'writes' : randrange(1024,16384,3),
                                              }
                                             )
                    except ManagementTarget.DoesNotExist:
                        pass
                    try:
                        mdt = MetadataTarget.objects.get(filesystem = fs)
                        volume_list.append(
                                           {
                                            'timestamp' : slice,
                                            'targetname' : mdt.name,
                                            'writes' : randrange(1024,16384,3),
                                           }
                                          )
                    except MetadataTarget.DoesNotExist:
                        pass
                    try:
                        osts = ObjectStoreTarget.objects.filter(filesystem = fs)
                        for ost in osts:
                            for slice in current_slice:
                                data_slice.append(
                                                  {
                                                   'timestamp' : slice,
                                                   'targetname' : ost.name,
                                                   'writes' : randrange(1024,16384,3),
                                                  }
                                                 )
                    except:
                        pass
                    return data_slice
        #except:
        #    raise Exception('POST call API_Exception:get_target_writes(target_name,start_time,end_time ,data_function) => Failed to get data for inputs targetname=%s|starttime=%s|endtime%s |datafunction=%s' %target_name %start_time %end_time   %data_function)


