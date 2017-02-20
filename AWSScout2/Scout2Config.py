# Import future stuff...
from __future__ import print_function
from __future__ import unicode_literals


import json

from AWSScout2.ServicesConfig import ServicesConfig
from AWSScout2.utils import *

class Scout2Config(object):
    """
    Root object that holds all of the necessary AWS resources and Scout2
    configuration items.

    :account_id         AWS account ID
    :last_run           Information about the last run
    :metadata           Metadata used to generate the HTML report
    :ruleset            Ruleset used to perform the analysis
    :services           AWS configuration sorted by service
    """

    def __init__(self, services = [], skipped_services = []):
        self.account_id = None
        self.last_run = None
        self.__load_metadata()
        supported_services = []
        for group in self.metadata:
            for service in self.metadata[group]:
                supported_services.append(service)
        self.service_list = self.__build_services_list(supported_services, services, skipped_services)
        self.services = ServicesConfig()


    def fetch(self, credentials, regions = [], skipped_regions = [], partition_name = 'aws'):
        """

        :param credentials:
        :param services:
        :param skipped_services:
        :param regions:
        :param skipped_regions:
        :param partition_name:
        :return:
        """
        # TODO: determine partition name based on regions and warn if multiple partitions...

        self.services.fetch(credentials, self.service_list, regions, partition_name)


    def __load_metadata(self):
        # Load metadata
        with open('metadata.json', 'rt') as f:
            self.metadata = json.load(f)

    def save_to_file(self, environment_name, force_write = False, debug = False, js_filename = 'aws_config', js_varname = 'aws_info', quiet = False):
        print('Saving config to %s' % js_filename)
        try:
            with open_file(environment_name, force_write, js_filename, quiet) as f:
                print('%s =' % js_varname, file = f)
                print('%s' % json.dumps(vars(self), indent=4 if debug else None, separators=(',', ': '), sort_keys=True, cls=Scout2Encoder), file = f)
        except Exception as e:
            printException(e)
            pass

    def __build_services_list(self, supported_services, services, skipped_services):
        return [s for s in supported_services if (services == [] or s in services) and s not in skipped_services]

    def update_metadata(self):
        service_map = {}
        for service_group in self.metadata:
            for service in self.metadata[service_group]:
                if service not in self.service_list:
                    continue
                if 'resources' not in self.metadata[service_group][service]:
                    continue
                service_map[service] = service_group
                for resource in self.metadata[service_group][service]['resources']:
                    # full_path = path if needed
                    if not 'full_path' in self.metadata[service_group][service]['resources'][resource]:
                        self.metadata[service_group][service]['resources'][resource]['full_path'] = self.metadata[service_group][service]['resources'][resource]['path']
                    # Script is the full path minus "id" (TODO: change that)
                    if not 'script' in self.metadata[service_group][service]['resources'][resource]:
                        self.metadata[service_group][service]['resources'][resource]['script'] = '.'.join([x for x in self.metadata[service_group][service]['resources'][resource]['full_path'].split('.') if x != 'id'])
                    # Update counts
                    count = '%s_count' % resource
                    service_config = getattr(self.services, service)

                    if service_config and resource != 'regions':
                      if hasattr(service_config, 'regions'):
                        self.metadata[service_group][service]['resources'][resource]['count'] = 0
                        for region in service_config.regions:
                            if hasattr(service_config.regions[region], count):
                                self.metadata[service_group][service]['resources'][resource]['count'] += getattr(service_config.regions[region], count)
                      else:
                        self.metadata[service_group][service]['resources'][resource]['count'] = getattr(service_config, count)


    def finalize(self, aws_config, current_time, args):
        # Set AWS account ID
        aws_config['account_id'] = 'TODO' # get_aws_account_id(self.services['iam'])
        # Save info about run
        aws_config['last_run'] = {}
        aws_config['last_run']['time'] = current_time.strftime("%Y-%m-%d %H:%M:%S%z")
        aws_config['last_run']['cmd'] = ' '.join(args)
        aws_config['last_run']['version'] = __version__
        #aws_config['last_run']['ruleset_name'] = ruleset_filename.replace('rulesets/', '').replace('.json', '')
        #aws_config['last_run']['ruleset_about'] = ruleset['about'] if 'about' in ruleset else ''


