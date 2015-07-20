#!/usr/bin/env python
""" VISSIM Tools v.0. """
import re, math
from numpy import median
def line_process(line):
    """ Process VISSIM text such that double quotations don't get split by
    space delimiter.
    """
    if '"' in line:
        matches = re.findall(r'\"(.+?)\"', line)
        matchblank = re.findall(r'\"(.?)\"', line)
        final_line = []
        line = line.split('"')
        for i in line:
            if i in matches:
                final_line.append('"' + i + '"')
                matches.remove(i)
            elif i in matchblank:
                final_line.append('""')
                matchblank.remove(i)
            else:
                final_line += i.split()
        return final_line
    else:
        return line.strip().split()
class Inputs:
    """ Handles Inputs section of .INP file.
    """
    def __init__(self,filename):
        self.filename = filename
        self.name = 'Inputs'
        self.inputs_data = {}
        self.current_input = None
        self.current_input_number = None
        self.current_input_name = None
        self.count = 0
        self.data = None
        self.import_inputs()
    def read_inputs(self, line):
        """ Process the Input section of the INP file.
        """
        inputs_data = self.inputs_data
        if line[0] == 'INPUT':
            self.current_input_number = line[1]
        elif line[0] == 'NAME':
            self.current_input_name = line[1]
        elif line[0] == 'LINK':
            self.current_input = line[1]
            if self.inputs_data.has_key(self.current_input):
                self.count = len(self.inputs_data[self.current_input])
                self.inputs_data[self.current_input].append({})
                self.data = self.inputs_data[self.current_input][self.count]
            else:
                self.count = 0
                inputs_data[self.current_input] = [{}]
                self.data = self.inputs_data[self.current_input][self.count]
            current_demand = line[4]
            current_comp = line[6]
            self.data['name'] = self.current_input_name
            self.data['input'] = self.current_input_number
            self.data['Q'] = current_demand
            self.data['composition'] = current_comp
        elif line[0] == 'TIME':
            self.data['from'] = line[2]
            self.data['until'] = line[4]
    def import_inputs(self):
        """ Imports Input syntax into dictionary.
        """
        filename = self.filename
        try:
            with open(filename, "r") as data:
                section = None
                for row in data:
                    line = line_process(row)
                    if len(line) == 0:
                        continue
                    elif line[0] == '--':
                        section = line[1]
                    elif section == "Inputs:":
                        self.read_inputs(line)
                    else:
                        continue
        except IOError:
            print 'cannot open', filename
    def output_inputs(self, inputs):
        """ Outputs Inputs syntax to VISSIM.

        Input: A single Inputs dictionary
        Output: Inputs back into VISSIM syntax
        """
        vissim_out = []
        vissim_out.append('INPUT ' + str(inputs['input']).rjust(6))
        vissim_out.append('NAME '.rjust(10) + inputs['name'] + ' LABEL  ' + inputs['label'][0] + inputs['label'][1])
        vissim_out.append('LINK '.rjust(10) + ' Q ' + str(inputs['Q']) + ' COMPOSITION ' + str(inputs['composition']))
        vissim_out.append('TIME FROM '.rjust(15) + inputs['from'] + ' UNTIL ' + inputs['until'])
        return vissim_out
    def create_inputs(self, link, demand, composition, **kwargs):
        if kwargs.has_key('inputs'):
            inputs_num = kwargs['inputs']
        else:
            inputs_num = max(self.inputs_data.keys())+1
        self.inputs_data[inputs_num] = {}
        inputs = self.inputs_data[inputs_num]
        self.inputs_data['inputs'] = inputs_num
        self.inputs_data['Q'] = demand
        self.inputs_data['link'] = link
        self.inputs_data['composition'] = composition
        # Default values
        self.inputs_data['name'] = '""'
        self.inputs_data['label'] = ['0.00', '0.00']
        self.inputs_data['from'] = [0.000]
        self.inputs_data['until'] = [3600.00]
        assert len(self.inputs_data['from']) == len(self.inputs_data['to']) ==len(self.inputs_data['Q']) == len(self.inputs_data['composition'])
class Links:
    """ Handles Links section of .INP file.
    """
    def __init__(self, filename):
        self.filename = filename
        self.name = 'Links'
        self.links_data = {}
        self.current_link = None
        self.over = None
        self.links = None
        self.import_links()
    def read_links(self, line):
        if line[0] == 'LINK':
            self.current_link = int(line[1])
            self.links_data[self.current_link] = {}
            self.links = self.links_data[self.current_link]
            self.links['link'] = self.current_link
            self.links['name'] = line[3]
            self.links['label'] = [line[5], line[6]]
            self.over = False
        if line[0] == 'BEHAVIORTYPE':
            self.links['behaviortype'] = line[1]
            self.links['displaytype'] = line[3]
        if line[0] == 'LENGTH':
            self.links['length'] = line[1]
            self.links['lanes'] = line[3]
            self.links['lane_width'] = []
            count = 4
            if int(line[3]) > 1:
                for i in range(0, int(line[3])):
                    self.links['lane_width'].append(line[5+i])
                    count += 1
            else:
                self.links['lane_width'] = [line[5]]
                count += 1
            self.links['gradient'] = line[count+2]
            self.links['cost'] = line[count+4]
            self.links['surcharge1'] = line[count+6]
            self.links['segment_length'] = line[count+11]
            if line[-1] == 'EVALUATION':
                self.links['evaluation'] = ' EVALUATION'
            else:
                self.links['evaluation'] = ''
        if line[0] == 'FROM':
            self.links['from'] = (float(line[1]), float(line[2]))
        if line[0] == 'TO':
            self.links['to'] = (float(line[1]), float(line[2]))
        if line[0] == 'OVER' and self.over == False:
            self.links['over'] = []
            size = int(len(line)/float(4))
            for coord in range(0, size):
                x = float(line[(4*coord)+1])
                y = float(line[(4*coord)+2])
                self.links['over'].append((x,y))
            self.over = True
        elif line[0] == 'OVER' and self.over == True:
            size = int(len(line)/float(4))
            for coord in range(0, size):
                x = float(line[(4*coord)+1])
                y = float(line[(4*coord)+2])
                self.links['over'].append((x,y))
    def import_links(self):
        """ Imports Links syntax into dictionary.
        """
        filename = self.filename
        try:
            with open(filename, "r") as data:
                section = None
                for row in data:
                    line = line_process(row)
                    if len(line) == 0:
                        continue
                    elif line[0] == '--':
                        section = line[1]
                    elif section == "Links:":
                        self.read_links(line)
                    else:
                        continue
                return self.links_data
        except IOError:
            print 'cannot open', filename
    def output_links(self, links):
        """ Outputs Links syntax to VISSIM.

        Input: A single links dictionary
        Output: Route decisions back into VISSIM syntax
        """
        vissim_out = []
        vissim_out.append('LINK ' + str(links['link']).rjust(6) + ' NAME ' + links['name'] + ' LABEL ' + links['label'][0] + ' ' + links['label'][1])
        vissim_out.append('BEHAVIORTYPE '.rjust(15) + links['behaviortype'].rjust(5) + ' DISPLAYTYPE' + links['displaytype'].rjust(5))
        lane_width_str = ''
        if len(links['lane_width']) > 1:
            for width in links['lane_width']:
                lane_width_str += width.rjust(5)
        else:
            lane_width_str = links['lane_width'][0].rjust(5)
        vissim_out.append('LENGTH '.rjust(9) + str(links['length']).rjust(8) + ' LANES ' + links['lanes'].rjust(2) + ' LANE_WIDTH ' + lane_width_str + ' GRADIENT ' + links['gradient'].ljust(10) + ' COST ' + links['cost'].ljust(7) + ' SURCHARGE ' + links['surcharge1'] + ' SURCHARGE ' + links['surcharge1'] + ' SEGMENT LENGTH ' + links['segment_length'].rjust(8) + links['evaluation'])
        vissim_out.append('FROM '.rjust(7) + str(links['from'][0]) + ' ' + str(links['from'][1]))
        if links.has_key('over'):
            over_str = ' '
            for i in links['over']:
                over_str += ' OVER ' + str(i[0]) + ' ' + str(i[1]) + ' 0.000'
            vissim_out.append(over_str)
        vissim_out.append('TO '.rjust(5) + str(links['to'][0]).rjust(10) + ' ' + str(links['to'][1]))
        return vissim_out
    def export_links(self, filename):
        """ Prepare for export all links in a given links object

            Input: Links object
            Output: List of all links in VISSIM syntax
        """
        links_data = self.links_data
        print_data = []
        open(filename, 'w').write('-- Links: --\n------------\n')
        for key, value in links_data.items():
            print_data = self.output_links(value)
            for line in print_data:
                open(filename, 'a').write(str(line) + '\n')
    def create_link(self, coord_from, coord_to, **kwargs):
        if kwargs.has_key('link'):
            link_num = kwargs['link']
        else:
            link_num = max(self.links_data.keys())+1
        self.links_data[link_num] = {}
        link = self.links_data[link_num]
        link['link'] = link_num
        link['from'] = coord_from
        link['to'] = coord_to
        # Default values
        link['name'] = '""'
        link['behaviortype'] = '1'
        link['cost'] = '0.00000'
        link['displaytype'] = '1'
        link['gradient'] = '0.00000'
        link['label'] = ['0.00', '0.00']
        link['lane_width'] = ['3.66']
        link['lanes'] = '1'
        link['segment_length'] = '10.000'
        link['surcharge1'] = '0.00000'
        link['evaluation'] = ''
        # User defined changes to the default values
        for name, value in kwargs.items():
            link[name] = value
        if link.has_key('over'):
            link['length'] = 0
            x1, y1 = link['from']
            for coord in link['over']:
                x2, y2 = coord
                dx, dy = x2-x1, y2-y1
                link['length'] += math.sqrt(dx**2 + dy**2)
                x1, y1 = x2, y2
            link['length'] = str(round(link['length'], 3))
        else:
            link['length'] = str(round(math.sqrt((link['to'][0]-link['from'][0])**2 + (link['to'][1]-link['from'][1])**2), 3))
class Connector:
    """ Handles Connector section of .INP file.
    """
    def __init__(self, filename):
        self.filename = filename
        self.name = 'Connector'
        self.connector_data = {}
        self.current_connector = None
        self.connector = None
        self.import_connector()
    def read_connector(self, line):
        if line[0] == 'CONNECTOR':
            self.current_connector = int(line[1])
            self.connector_data[self.current_connector] = {}
            self.connector = self.connector_data[self.current_connector]
            self.connector['connector'] = self.current_connector
            self.connector['name'] = line[3]
            self.connector['label'] = [line[5], line[6]]
        elif line[0] == 'FROM':
            if len(line) == 7:
                self.connector['from'] = line[2]
                self.connector['from_lanes'] = [line[4]]
                self.connector['from_at'] = line[6]
            else:
                lane_num = len(line) - 7
                self.connector['from'] = line[2]
                self.connector['from_lanes'] = [line[4]]
                for lanes in range(1, lane_num+1):
                    self.connector['from_lanes'].append(line[4+lanes])
                self.connector['from_at'] = line[6+lane_num]
        elif line[0] == 'OVER':
            if self.connector.has_key('over'):
                overs = len(line)/4
                for num in range(0,overs):
                    self.connector['over'].append((line[(num*4)+1],line[(num*4)+2]))
            else:
                self.connector['over'] = []
                overs = len(line)/4
                for num in range(0,overs):
                    self.connector['over'].append((line[(num*4)+1],line[(num*4)+2]))
        elif line[0] == 'TO':
            if len(line) == 12:
                self.connector['to'] = line[2]
                self.connector['to_lanes'] = [line[4]]
                self.connector['to_at'] = line[6]
                self.connector['behaviortype'] = line[8]
                self.connector['displaytype'] = line[10]
            else:
                lane_num = len(line) - 12
                self.connector['to'] = line[2]
                self.connector['to_lanes'] = [line[4]]
                for lanes in range(1, lane_num+1):
                    self.connector['to_lanes'].append(line[4+lanes])
                self.connector['to_at'] = line[6+lane_num]
                self.connector['behaviortype'] = line[8+lane_num]
                self.connector['displaytype'] = line[10+lane_num]
        elif line[0] == 'DX_EMERG_STOP':
            self.connector['dx_emerg_stop'] = line[1]
            self.connector['dx_lane_change'] = line[3]
        elif line[0] == 'GRADIENT':
            self.connector['gradient'] = line[1]
            self.connector['cost'] = line[3]
            self.connector['surcharge1'] = line[5]
            self.connector['surcharge2'] = line[7]
        elif line[0] == 'SEGMENT':
            self.connector['segment_length'] = line[2]
            if line[3] == 'NONE':
                self.connector['visualization'] = False
            else:
                self.connector['visualization'] = True
        else:
            print 'Non-connector data provided'
    def import_connector(self):
        """ Imports connector syntax into dictionary.
        """
        filename = self.filename
        try:
            with open(filename, "r") as data:
                section = None
                for row in data:
                    line = line_process(row)
                    if len(line) == 0:
                        continue
                    elif line[0] == '--':
                        section = line[1]
                    elif section == "Connectors:":
                        self.read_connector(line)
                    else:
                        continue
                return self.connector_data
        except IOError:
            print 'cannot open', filename
    def output_connector(self, connector):
        """ Outputs connector syntax to VISSIM.

        Input: A single connector dictionary
        Output: connector back into VISSIM syntax
        """
        vissim_out = []
        vissim_out.append('CONNECTOR ' + str(connector['connector']) + ' NAME ' + connector['name'] + ' LABEL ' + connector['label'][0] + ' ' + connector['label'][1])
        from_lanes_str = ''
        for i in connector['from_lanes']:
            from_lanes_str += i + ' '
        vissim_out.append('FROM LINK '.rjust(12) + str(connector['from']) + ' LANES ' + from_lanes_str + 'AT ' + connector['from_at'])
        over_str = ''
        for i in connector['over']:
            over_str += 'OVER ' + str(i[0]) + ' ' + str(i[1]) + ' 0.000 '
        vissim_out.append('  ' + over_str)
        to_lanes_str = ''
        for i in connector['to_lanes']:
            to_lanes_str += i + ' '
        vissim_out.append('TO LINK '.rjust(10) + str(connector['to']) + ' LANES '.rjust(7) + to_lanes_str + 'AT ' + connector['to_at'].ljust(6) + ' BEHAVIORTYPE ' + connector['behaviortype'] + ' DISPLAYTYPE ' + connector['displaytype'] + ' ALL')
        vissim_out.append('DX_EMERG_STOP '.rjust(16) + connector['dx_emerg_stop'] + ' DX_LANE_CHANGE ' + connector['dx_lane_change'])
        vissim_out.append('GRADIENT '.rjust(11) + connector['gradient'] + ' COST ' + connector['cost'] + ' SURCHARGE ' + connector['surcharge1'] + ' SURCHARGE ' + connector['surcharge2'])
        if connector['visualization'] == False:
            vissim_out.append('SEGMENT LENGTH '.rjust(17) + connector['segment_length'] + ' NONE ANIMATION')
        else:
            vissim_out.append('SEGMENT LENGTH '.rjust(17) + connector['segment_length'] + ' ANIMATION')
        return vissim_out
    def export_connector(self, filename):
        """ Prepare for export all connector lots in a given connector object

            Input: connector object
            Output: List of all connector lots in VISSIM syntax
        """
        connector_data = self.connector_data
        print_data = []
        open(filename, 'w').write('-- Connectors: --\n-----------------\n')
        for key, value in connector_data.items():
            print_data = self.output_connector(value)
            for line in print_data:
                open(filename, 'a').write(str(line) + '\n')
    def create_connector(self, linksobj, from_link, to_link, **kwargs):
        if kwargs.has_key('num'):
            connector_num = int(kwargs['num'])
        else:
            connector_num = max(self.connector_data.keys())+1
        self.connector_data[connector_num] = {}
        connector = self.connector_data[connector_num]
        connector['connector'] = connector_num
        connector['from'] = from_link
        connector['to'] = to_link
        # Default values
        connector['label'] = ['0.00', '0.00']
        connector['from_lanes'] = '1'
        connector['from_at'] = linksobj.links_data[from_link]['length']
        over1 = linksobj.links_data[from_link]['to']
        over4 = linksobj.links_data[to_link]['from']
        if over4[0] == over1[0] and over4[1] == over1[1]:
            over1 = (linksobj.links_data[from_link]['to'][0], linksobj.links_data[from_link]['to'][1]+0.001)
            over2 = (over4[0]+0.001, over4[1])
            over3 = (median([over2[0], over4[0]]), median([over2[1], over4[1]]))
        else:
            over2 = (median([over4[0], over1[0]]), median([over4[1], over1[1]]))
            over3 = (median([over2[0], over4[0]]), median([over2[1], over4[1]]))
        connector['over'] = [over1, over2, over3, over4]
        connector['name'] = '""'
        connector['to_lanes'] = '1'
        connector['to_at'] = '0.000'
        connector['behaviortype'] = '1'
        connector['displaytype'] = '1'
        connector['dx_emerg_stop'] = '4.999'
        connector['dx_lane_change'] = '200.010'
        connector['gradient'] = '0.00000'
        connector['cost'] = '0.00000'
        connector['surcharge1'] = '0.00000'
        connector['surcharge2'] = '0.00000'
        connector['segment_length'] = '10.000'
        connector['visualization'] = True
        # User defined changes to the default values
        for name, value in kwargs.items():
            connector[name] = value
class Parking:
    """ Handles Parking section of .INP file.
    """
    def __init__(self, filename):
        self.filename = filename
        self.name = 'Parking'
        self.parking_data = {}
        self.current_parking = None
        self.parking = None
        self.import_parking()
    def read_parking(self, line):
        if line[0] == 'PARKING_LOT':
            self.current_parking = int(line[1])
            self.parking_data[self.current_parking] = {}
            self.parking = self.parking_data[self.current_parking]
            self.parking['parking'] = self.current_parking
            self.parking['name'] = line[3]
            self.parking['label'] = [line[5], line[6]]
        elif line[0] == 'PARKING_SPACES':
            self.parking['spaces_length'] = line[2]
        elif line[0] == 'ZONES':
            self.parking['zones'] = line[1]
            self.parking['fraction'] = line[3]
        elif line[0] == 'POSITION':
            self.parking['position_link'] = line[2]
            if len(line) == 7:
                self.parking['lane'] = line[4]
                self.parking['at'] = line[6]
            elif len(line) == 5:
                self.parking['at'] = line[4]
        elif line[0] == 'LENGTH':
            self.parking['length'] = line[1]
        elif line[0] == 'CAPACITY':
            self.parking['capacity'] = line[1]
        elif line[0] == 'OCCUPANCY':
            self.parking['occupancy'] = line[1]
        elif line[0] == 'DEFAULT':
            self.parking['desired_speed'] = line[2]
        elif line[0] == 'OPEN_HOURS':
            self.parking['open_hours'] = (line[2], line[4])
        elif line[0] == 'MAX_TIME':
            self.parking['max_time'] = line[1]
        elif line[0] == 'FLAT_FEE':
            self.parking['flat_fee'] = line[1]
        elif line[0] == 'FEE_PER_HOUR':
            self.parking['fee_per_hour'] = line[1]
        elif line[0] == 'ATTRACTION':
            self.parking['attraction'] = line[1]
        elif line[0] == 'COMPOSITION':
            self.parking['composition'] = line[1]
        elif line == "":
            pass
        else:
            print 'Non-parking data provided'
    def import_parking(self):
        """ Imports Parking syntax into dictionary.
        """
        filename = self.filename
        try:
            with open(filename, "r") as data:
                section = None
                for row in data:
                    line = line_process(row)
                    if len(line) == 0:
                        continue
                    elif line[0] == '--':
                        section = line[1]
                    elif section == "Parking":
                        self.read_parking(line)
                    else:
                        continue
                return self.parking_data
        except IOError:
            print 'cannot open', filename
    def output_parking(self, parking):
        """ Outputs Parking syntax to VISSIM.

        Input: A single parking dictionary
        Output: Parking back into VISSIM syntax
        """
        vissim_out = []
        vissim_out.append('PARKING_LOT ' + str(parking['parking']) + ' NAME ' + parking['name'] + ' LABEL ' + parking['label'][0] + ' ' + parking['label'][1])
        if parking.has_key('spaces_length'):
            vissim_out.append('PARKING_SPACES LENGTH '.rjust(24) + parking['spaces_length'])
        vissim_out.append('ZONES '.rjust(8) + parking['zones'].rjust(6) + ' FRACTION ' + parking['fraction'].rjust(7))
        if parking.has_key('lane'):
            vissim_out.append('POSITION LINK '.rjust(16) + str(parking['position_link']) + ' LANE ' + str(parking['lane']) + ' AT ' + str(parking['at']))
        else:
            vissim_out.append('POSITION LINK '.rjust(16) + str(parking['position_link']) + ' AT ' + str(parking['at']))
        vissim_out.append('LENGTH '.rjust(9) + str(parking['length']).rjust(9))
        vissim_out.append('CAPACITY   '.rjust(13) + parking['capacity'])
        vissim_out.append('OCCUPANCY '.rjust(12) + parking['occupancy'])
        vissim_out.append('DEFAULT DESIRED_SPEED '.rjust(24) + parking['desired_speed'])
        vissim_out.append('OPEN_HOURS  FROM '.rjust(19) + parking['open_hours'][0].ljust(2) + ' UNTIL ' + parking['open_hours'][1])
        vissim_out.append('MAX_TIME '.rjust(11) + parking['max_time'])
        vissim_out.append('FLAT_FEE '.rjust(11) + parking['flat_fee'])
        vissim_out.append('FEE_PER_HOUR '.rjust(15) + parking['fee_per_hour'])
        vissim_out.append('ATTRACTION '.rjust(13) + parking['attraction'])
        if parking.has_key('composition'):
            vissim_out.append('COMPOSITION '.rjust(14) + parking['composition'])
        return vissim_out
    def export_parking(self, filename):
        """ Prepare for export all parking lots in a given parking object

            Input: Parking object
            Output: List of all parking lots in VISSIM syntax
        """
        parking_data = self.parking_data
        print_data = []
        open(filename, 'w').write('-- Parking Lots: --\n-------------------\n')
        for key, value in parking_data.items():
            print_data = self.output_parking(value)
            for line in print_data:
                open(filename, 'a').write(str(line) + '\n')
    def create_parking(self, linksobj, link, length, at, lane, **kwargs):
        if kwargs.has_key('num'):
            parking_num = int(kwargs['num'])
        else:
            parking_num = max(self.parking_data.keys())+1
        self.parking_data[parking_num] = {}
        parking = self.parking_data[parking_num]
        parking['parking'] = parking_num
        parking['lane'] = lane
        parking['at'] = at
        parking['position_link'] = link
        parking['length'] = length
        # Default values
        parking['name'] = ''
        parking['label'] = ['0.000', '0.000']
        parking['spaces_length'] = '6.000'
        parking['zones'] = ''
        parking['fraction'] = '1.000'
        parking['capacity'] = '100'
        parking['occupancy'] = '0'
        parking['desired_speed'] = '999'
        parking['open_hours'] = ('0', '99999')
        parking['max_time'] = '99999'
        parking['flat_fee'] = '0.0'
        parking['fee_per_hour'] = '0.0'
        parking['attraction'] = '0.0 0.0'
        parking['composition'] = '1'
        # User defined changes to the default values
        for name, value in kwargs.items():
            parking[name] = value
class Transit:
    """ Handles Transit section of .INP file.
    """
    def __init__(self, filename):
        self.filename = filename
        self.name = 'Transit'
        self.transit_data = {}
        self.current_line = None
        self.current_route = None
        self.current_name = None
        self.current_priority = None
        self.current_length = None
        self.current_mdn = None
        self.current_pt = False
        self.data = None
        self.import_transit()
    def read_transit(self, line):
        """ Process the Transit Decision section of the INP file
        """
        if line[0] == "LINE":
            self.current_name = line[3]
            self.current_line = line[1]
            self.current_route = line[7]
            self.current_priority = line[9]
            self.current_length = line[11]
            self.current_mdn = line[13]
            if len(line) == 14:
                self.current_pt = True
        elif line[0] == "ANM_ID":
            # Dictionary key is the line number
            self.transit_data[int(self.current_line)] = {}
            self.data = self.transit_data[int(self.current_line)]
            self.data['name'] = self.current_name
            self.data['line'] = self.current_line
            self.data['route'] = self.current_route
            self.data['priority'] = self.current_priority
            self.data['length'] = self.current_length
            self.data['mdn'] = self.current_mdn
            self.data['pt'] = self.current_pt
            self.data['link'] = line[4]
            self.data['desired_speed'] = line[6]
            self.data['vehicle_type'] = line[8]
        elif line[0] == "COLOR":
            self.data['color'] = line[1]
            self.data['time_offset'] = line[3]
        elif line[0] == "DESTINATION":
            self.data['destination_link'] = line[2]
            self.data['at'] = line[4]
        elif line[0] == "START_TIMES":
            self.data['start_times'] = []
            num = (len(line)-1)/5
            for i in range(0, num):
                self.data['start_times'].append([line[1+(5*i)], line[3+(5*i)], line[5+(5*i)]])
        elif line[1] == "COURSE":
            num = (len(line)/5)
            for i in range(0, num):
                self.data['start_times'].append([line[(5*i)], line[2+(5*i)], line[4+(5*i)]])
    def import_transit(self):
        """ Imports transit Decision syntax into dictionary.
        """
        filename = self.filename
        try:
            with open(filename, "r") as data:
                section = None
                for row in data:
                    line = line_process(row)
                    if len(line) <= 1:
                        continue
                    elif line[0] == '--':
                        section = line[1]
                    elif section == "Public":
                        self.read_transit(line)
                    else:
                        continue
                return self.transit_data
        except IOError:
            print 'cannot open', filename
    def output_transit(self, transit):
        """ Outputs transit Decision syntax to VISSIM.

        Input: A single transit decision dictionary
        Output: transit decisions back into VISSIM syntax
        """
        vissim_out = []
        pt = ''
        if transit['pt'] == True:
            pt = ' PT_TELE'
        vissim_out.append(str('LINE ' + transit['line'].rjust(4) + ' NAME ' + transit['name'] + '  LINE ' + transit['line'].rjust(3) + '  ROUTE ' + transit['route'].rjust(3) + '    PRIORITY ' + transit['priority'] + '  LENGTH ' + transit['length'] + '  MDN ' + transit['mdn']) + pt + '\n')
        vissim_out.append(str('ANM_ID '.rjust(12) + transit['anm'] +' SOURCE    LINK ' + transit['link'] + ' DESIRED_SPEED ' + transit['desired_speed'] + ' VEHICLE_TYPE ' + transit['vehicle_type']))
        vissim_out.append(str('COLOR '.rjust(24) + transit['color'] + ' TIME_OFFSET ' + transit['time_offset'].rjust(6)))
        vissim_out.append(str('DESTINATION    LINK '.rjust(32) + transit['destination_link'] +' AT ' + transit['at'].rjust(8)))
        time_str = 'START_TIMES '.rjust(24)
        count = 1
        for i in transit['start_times']:
            time_str += str(i[0] + ' COURSE ' + i[1] + ' OCCUPANCY ' + i[2] + ' ')
            if count % 5 == 0:
                time_str += '\n'
            count += 1
        if len(transit['start_times']) > 0:
            vissim_out.append(time_str)
        return vissim_out
    def export_transit(self, filename):
        """ Prepare for export all transit routes in a given transit object

            Input: transit object
            Output: List of all transit lots in VISSIM syntax
        """
        transit_data = self.transit_data
        print_data = []
        open(filename, 'w').write('-- Public Transport: --\n-----------------\n')
        for key, value in transit_data.items():
            print_data = self.output_transit(value)
            for line in print_data:
                open(filename, 'a').write(str(line) + '\n')
    def create_transit(self, link, dest_link, at, desired_speed, vehicle_type, **kwargs):
        if kwargs.has_key('num'):
            transit_num = int(kwargs['num'])
        elif len(self.transit_data.keys()) >= 1:
            transit_num = max(self.transit_data.keys())+1
        else:
            transit_num = 1
        self.transit_data[transit_num] = {}
        transit = self.transit_data[transit_num]
        transit['line'] = str(transit_num)
        transit['link'] = str(link)
        transit['at'] = str(at)
        transit['destination_link'] = str(dest_link)
        transit['desired_speed'] = str(desired_speed)
        transit['vehicle_type'] = str(vehicle_type)
        # Default values
        transit['anm'] = '""'
        transit['name'] = '""'
        transit['route'] = '0'
        transit['priority'] = '0'
        transit['length'] = '0'
        transit['mdn'] = '0'
        transit['pt'] = False
        transit['color'] = 'CYAN'
        transit['time_offset'] = '0.0'
        transit['start_times'] = []
        # User defined changes to the default values
        for name, value in kwargs.items():
            transit[name] = value
class Routing:
    """ Handles Route Decision section of .INP file.
    """
    def __init__(self, filename):
        self.filename = filename
        self.name = 'Routing Decisions'
        self.routing_data = {}
        self.current_dec = None
        self.current_route = None
        self.current_name = None
        self.current_number = None
        self.current_label = None
        self.time_periods = None
        self.current_link_location = None
        self.current_vehicle_class = None
        self.over = None
        self.count = None
        self.data = None
        self.import_route()
    def routing(self,line,links=True,link_key=False):
        """ Process the Route Decision section of the INP file
        """
        if line[0] == "ROUTING_DECISION":
            self.current_name = line[3]
            self.current_number = line[1]
            self.current_label = [line[5], line[6]]
            self.over = False
        elif line[0] == "LINK":
            self.current_dec = line[1]
            self.current_link_location = line[3]
            # Dictionary key is either link number or routing decision number
            if link_key == True:
                dict_key = self.current_dec
            else:
                dict_key = self.current_number
            if self.routing_data.has_key(dict_key):
                self.count = len(self.routing_data[dict_key])
                self.routing_data[dict_key].append({})
                self.data = self.routing_data[dict_key][self.count]
            else:
                self.count = 0
                self.routing_data[dict_key] = [{}]
                self.data = self.routing_data[dict_key][self.count]
            self.data['link'] = self.current_dec
            self.data['route'] = {}
            self.data['name'] = self.current_name
            self.data['number'] = self.current_number
            self.data['label'] = self.current_label
            self.data['at'] = self.current_link_location
        elif line[0] == "TIME":
            self.time_periods = (len(line)-1)/4
            self.data['time'] = []
            for i in range(0, self.time_periods):
                start = line[2+(4*i)]
                end = line[4+(4*i)]
                self.data['time'].append((start, end))
        elif line[0] == "VEHICLE_CLASSES":
            self.current_vehicle_class = line[1]
            self.data['vehicle_classes'] = self.current_vehicle_class
        elif line[0] == "PT":
            self.current_vehicle_class = line[1]
            self.data['PT'] = self.current_vehicle_class
        elif line[0] == "ALTERNATIVES":
            self.data['alternatives'] = True
        elif line[0] == "ROUTE":
            self.over = False
            self.current_route = line[1]
            destination_link = line[4]
            destination_at = line[6]
            self.data['route'][self.current_route] = {}
            self.data['route'][self.current_route]['destination link'] = destination_link
            self.data['route'][self.current_route]['at'] = destination_at
        elif line[0] == "FRACTION":
            self.data['route'][self.current_route]['fraction'] = []
            for i in range(0, self.time_periods):
                fraction = line[1+(i*2)]
                self.data['route'][self.current_route]['fraction'].append(fraction)
        elif line[0] == "OVER" and links is True:
            self.over = True
            self.data['route'][self.current_route]['over'] = line[1:]
        elif self.over is True and links is True:
            self.data['route'][self.current_route]['over'] += line
    def import_route(self,link_key=False):
        """ Imports Route Decision syntax into dictionary.
        """
        filename = self.filename
        try:
            with open(filename, "r") as data:
                section = None
                for row in data:
                    line = line_process(row)
                    if len(line) == 0:
                        continue
                    elif line[0] == '--':
                        section = line[1]
                    elif section == "Routing":
                        self.routing(line)
                    else:
                        continue
                return self.routing_data
        except IOError:
            print 'cannot open', filename
    def output_routing(self, route):
        """ Outputs Route Decision syntax to VISSIM.

        Input: A single route decision dictionary
        Output: Route decisions back into VISSIM syntax
        """
        vissim_out = []
        vissim_out.append(str('ROUTING_DECISION ' + route['number'].ljust(4) +
                              ' NAME ' + route['name'] + ' LABEL ' +
                              route['label'][0] + ' ' + route['label'][1]))
        vissim_out.append(str('LINK '.rjust(10) + route['link'] +'AT '.rjust(5)
                              + route['at']))
        time_str = 'TIME'.rjust(9)
        for i in route['time']:
            time_str += str('  FROM ' + i[0] + ' UNTIL ' + i[1])
        vissim_out.append(time_str)
        if route.has_key('vehicle_classes'):
            vissim_out.append('VEHICLE_CLASSES '.rjust(21) + route['vehicle_classes'])
        elif route.has_key('PT'):
            vissim_out.append('PT '.rjust(21) + route['PT'])
        for i in route['route']:
            vissim_out.append('ROUTE'.rjust(11) + i.rjust(6) + ' DESTINATION LINK'              + route['route'][i]['destination link'].rjust(6) +
                              ' AT' + route['route'][i]['at'].rjust(9))
            fraction_str = ''
            for j in route['route'][i]['fraction']:
                fraction_str += 'FRACTION '.rjust(16) + j
            vissim_out.append(fraction_str)
            link_count = 1
            # Sometimes the route ends on the same link it began:
            if route['route'][i].has_key('over') is False:
                break
            else:
                for j in route['route'][i]['over']:
                    if link_count == 1:
                        over_str = 'OVER '.rjust(11)
                        over_str += j.rjust(6)
                        link_count += 1
                        continue
                    elif link_count == len(route['route'][i]['over']):
                        over_str += j.rjust(6)
                        vissim_out.append(over_str)
                        break
                    elif (link_count % 10) == 0:
                        over_str += j.rjust(6)
                        vissim_out.append(over_str)
                        over_str = ' '*11
                        link_count += 1
                    else:
                        over_str += j.rjust(6)
                        link_count += 1
        return vissim_out
    def export_routing(self, routingobj):
        """ Prepare for export all routes in a given route object

            Input: Route object
            Output: List of all routes in VISSIM syntax
        """
        routing_data = routingobj.routing_data
        print_data = []
        for key in routing_data:
            if len(routing_data[key]) > 1:
                for dic in routing_data[key]:
                    print_data += self.output_routing(dic)
            else:
                print_data += self.output_routing(routing_data[key][0])
        return print_data
class Node:
    """ Handles Node section of .INP file.
    """
    def __init__(self, filename):
        self.filename = filename
        self.name = 'Node'
        self.node_data = {}
        self.current_node = None
        self.node = None
        self.import_node()
    def read_node(self, line):
        if line[0] == 'NODE':
            self.current_node = int(line[1])
            self.node_data[self.current_node] = {}
            self.node = self.node_data[self.current_node]
            self.node['node'] = self.current_node
            self.node['name'] = line[3]
            self.node['label'] = [line[5], line[6]]
        elif line[0] == 'EVALUATION':
            self.node['evaluation'] = line[1]
        elif line[0] == 'NETWORK_AREA':
            self.node['network_area'] = line[1]
            self.node['over'] = []
            overs = int(line[1])
            for num in range(0,overs):
                self.node['over'].append((line[(num*2)+2],line[(num*2)+3]))
        else:
            print 'Non-node data provided'
    def import_node(self):
        """ Imports node syntax into dictionary.
        """
        filename = self.filename
        try:
            with open(filename, "r") as data:
                section = None
                for row in data:
                    line = line_process(row)
                    if len(line) == 0:
                        continue
                    elif line[0] == '--':
                        section = line[1]
                    elif section == "Nodes:":
                        self.read_node(line)
                    else:
                        continue
                return self.node_data
        except IOError:
            print 'cannot open', filename
    def output_node(self, node):
        """ Outputs node syntax to VISSIM.

        Input: A single node dictionary
        Output: node back into VISSIM syntax
        """
        vissim_out = []
        vissim_out.append('NODE ' + str(node['node']) + ' NAME ' + node['name'] + ' LABEL ' + node['label'][0] + ' ' + node['label'][1])
        vissim_out.append('EVALUATION '.rjust(13) + node['evaluation'])
        over_str = ''
        over_count = 0
        if node.has_key('over'):
            for i in node['over']:
                over_str +=  '  ' + str(i[0]) + ' ' + str(i[1])
                over_count += 1
            vissim_out.append('NETWORK_AREA '.rjust(15) + str(over_count) + over_str)
        elif node.has_key('links'):
            for i in node['links']:
                over_str += '\nLINK '.rjust(10) + str(i).rjust(10)
            vissim_out.append('NETWORK_AREA'.rjust(16) + over_str)
        return vissim_out
    def export_node(self, filename):
        """ Prepare for export all node lots in a given node object

            Input: node object
            Output: List of all node lots in VISSIM syntax
        """
        node_data = self.node_data
        print_data = []
        open(filename, 'w').write('-- Nodes: --\n------------\n')
        for key, value in node_data.items():
            print_data = self.output_node(value)
            for line in print_data:
                open(filename, 'a').write(str(line) + '\n')
    def create_node_area(self, area, **kwargs):
        if kwargs.has_key('num'):
            node_num = int(kwargs['num'])
        elif len(self.node_data.keys()) == 0:
            node_num = 1
        else:
            node_num = max(self.node_data.keys())+1
        self.node_data[node_num] = {}
        node = self.node_data[node_num]
        node['node'] = node_num
        node['over'] = area
        node['network_area'] = len(area)
        # Default values
        node['name'] = '""'
        node['label'] = ['0.00', '0.00']
        node['evaluation'] = 'NO'
        # User defined changes to the default values
        for name, value in kwargs.items():
            node[name] = value
    def create_node_link(self, link, **kwargs):
        if kwargs.has_key('num'):
            node_num = int(kwargs['num'])
        elif len(self.node_data.keys()) == 0:
            node_num = 1
        else:
            node_num = max(self.node_data.keys())+1
        self.node_data[node_num] = {}
        node = self.node_data[node_num]
        node['node'] = node_num
        node['links'] = link
        # Default values
        node['name'] = '""'
        node['label'] = ['0.00', '0.00']
        node['evaluation'] = 'NO'
        # User defined changes to the default values
        for name, value in kwargs.items():
            node[name] = value
def get_section(datafile, sectionname):
    """ Returns the starting and ending line number for the desired section.

        Input: filename (INP), section name (routing, input)
        Output: starting line number, ending line number
    """
    foundsection = False
    sectionname = '-- ' + str(sectionname) + ': --'
    print sectionname
    endsection = ': --'
    for num, line in enumerate(datafile, 1):
        if line.strip() == sectionname:
            sectionnum = num + 1
            foundsection = True
        elif foundsection is True and endsection in line:
            endsectionnum = num - 2
            return sectionnum, endsectionnum
        else:
            continue
"""
def replace_section(datafile, sectionobj):
    """
""" Takes an INP file and replaces a section with a new section.

        Input: filename (INP), section object
        Output: new filename
    """
"""start, end = get_section(filename, sectionobj.name)
    del data[start:end+1]
    for i in export_routing(sectionobj):
        data.insert(start, i + '\n')
        start += 1
    newfilename = filename + '.new'
    open(newfilename, 'w+').writelines(data)
def export_data(filename, **objects):"""
""" find a file to edit, pass any number of sections to replace
    """
"""    data = open(filename).readlines()
    for key in objects:
"""
