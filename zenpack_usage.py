#! /opt/zenoss/bin/python

###########################
#   ZEP Facade Example    #
###########################
# Created by: Ryan Matte  #
# Updated by: Shane Scott #
###########################

# import the stuff that zendmd needs and create the dmd context
import Globals
from Products.ZenUtils.ZenScriptBase import ZenScriptBase
from transaction import commit
import datetime

dmd = ZenScriptBase(connect=True, noopts=True).dmd

# import the stuff that zep needs
from Products.Zuul import getFacade, listFacades
from zenoss.protocols.jsonformat import from_dict
from zenoss.protocols.protobufs.zep_pb2 import EventSummary
from Products.ZenEvents.events2.proxy import EventSummaryProxy

def scan_zenpacks():
    # Refactor as generator ?
    print('Scanning ZenPacks')
    data = dict()
    zenpackmgr = dmd.ZenPackManager
    packs = zenpackmgr['packs']
    zenpacks = packs.objectValues()
    for zp in zenpacks:
        zp_data = {
            'license': zp.license,
            'author': zp.author,
            'version': zp.version,
            'egg': zp.eggPack,
            'templates': [],
        }
        packables = zp['packables']
        zp_templates = []
        zp_templates = [o for o in packables.objectValuesAll() if o.meta_type == 'RRDTemplate']
        templates_data = []
        for t in zp_templates:
            templates_data.append({
                'id': t.id,
                'primaryId': t.getPrimaryId(),
                'targetPythonClass': t.targetPythonClass,
                'creation_time': t._created_timestamp,
                'in_use': False,
            })
        templates_data = sorted(templates_data, key=lambda t: t['id'])
        zp_data['templates'] = templates_data
        data[zp.id] = zp_data
        '''
        data.append({
            zp.id: zp_data,
        })
        '''
    return data

def scan_templates():
    print('Scanning templates in devices')

    def parse_templates(device, obj):
        for t in obj.getRRDTemplates():
            t_id = t.getPrimaryId()
            if t_id in templates_set:
                continue
            templates_set.add(t_id)
            t_zenpack = t.pack()
            if t_zenpack:
                t_zenpack_id = t_zenpack.id
            else:
                t_zenpack_id = 'None'

            data[t_id] = {'id': t.id,
                          'zenpack': t_zenpack_id,
                          'targetPythonClass': t.targetPythonClass,
                          'creation_time': t._created_timestamp,
                          'device': device.id,
                          'in_zenpack': False,
                         }

    data = dict()
    templates_set = set()
    for d in dmd.Devices.getSubDevices():
        parse_templates(d, d)
        comps = d.getDeviceComponents()
        for c in comps:
            parse_templates(d, c)
    return data

def report_templates(zenpacks_data, templates_data):
    with open('zenpack_usage.tsv', 'w') as output:
        output.write('\t'.join(['ZenPack', 'License', 'Author', 'Version', 'Egg', 'Template', 'Template UID',
                                'Python Class(ZP)', 'Creation Time(ZP)', 'ZenPack(T)', 'Python Class(T)', 'Device',
                                'Creation Time(ZP)\n']))
        for zp_id, zp_data in sorted(zenpacks_data.items()):
            print(zp_id)
            # print(zp_data)
            row_zp = [zp_id, zp_data['license'], zp_data['author'], zp_data['version'],
                      str(zp_data['egg'])]
            if zp_data['templates'] == []:
                output.write('\t'.join(row_zp))
                output.write('\n')
            for zt in sorted(zp_data['templates'], key=lambda i: i['id']):
                # print(zt)
                row = []
                row.extend(row_zp)
                creation_time = datetime.datetime.fromtimestamp(zt['creation_time']).strftime('%d/%m/%Y %H:%M')
                row.extend([zt['id'], zt['primaryId'], zt['targetPythonClass'], creation_time])
                if zt['primaryId'] in templates_data:
                    '''
                    '/zport/dmd/Devices/ControlCenter/devices/st-monlogcol-s01.staging.credoc.be/CC-Service-zenhubiworker': 
                    {'in_zenpack': False, 'creation_time': 1612865751.261312, 'zenpack': 'None', 
                    'targetPythonClass': 'ZenPacks.zenoss.ControlCenter.Service', 
                    'device': 'st-monlogcol-s01.staging.credoc.be', 'id': 'CC-Service-zenhubiworker'}
                    '''
                    t_data = templates_data[zt['primaryId']]
                    creation_time = datetime.datetime.fromtimestamp(t_data['creation_time']).strftime('%d/%m/%Y %H:%M')
                    row.extend([t_data['zenpack'], t_data['targetPythonClass'], t_data['device'], creation_time])
                    templates_data[zt['primaryId']]['in_zenpack'] = True
                else:
                    row.extend(['', '', '', ''])
                output.write('\t'.join(row))
                output.write('\n')

        # output templates not in zenpacks
        # TODO: Check whether templates has a parent template in a ZenPack
        for t_uid, t_data in sorted(templates_data.items()):
            if t_data['in_zenpack']:
                continue
            creation_time = datetime.datetime.fromtimestamp(t_data['creation_time']).strftime('%d/%m/%Y %H:%M')
            row = ['', '', '', '', '', t_data['id'], t_uid, '', '', t_data['zenpack'], t_data['targetPythonClass'],
                   t_data['device'], creation_time]
            # print(row)
            output.write('\t'.join(row))
            output.write('\n')
    return

# TODO: use generators to reduce memory footprint

if __name__ == '__main__':
    zenpacks_data = scan_zenpacks()
    templates_data = scan_templates()
    report_templates(zenpacks_data, templates_data)
