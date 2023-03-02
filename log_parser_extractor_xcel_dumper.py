# Krypto MTE parser and extractor for MS Azure Logs
# Author: Asif Nadaf
# intended ouput: 1) In Excel, values for microsecond values of 4 stages
#                 2) In Excel, values showing the deltas, packet received timestamp i.e Tx to Rx.
#                 3) In Excel, values showing the MS Azure deltas between the 1st state and last state, decoder init and decoder save states respectively.

import os       #importing os library for file operations
import re       #importing regex library
import json     #importing json library
import xlwt     #write to an excel sheet
from xlwt import Workbook
import xlsxwriter

azure_log_timestamp_example = '2022-11-20T06:43:49.557'
information_decode_succeed_time = '[Information] Executed \'Decode\' (Succeeded,' #using escape char \ to escape literal quotes surrounding Decode word
packet_anchor_start = 'Packet Received:'
packet_anchor_end = 'TOKBYTES'
unencrypted_device_packet_anchor_start = '[Information] Executing \'Decode\''
unencrypted_device_packet_anchor_end = 'Executed \'Decode\' (Succeeded'
deviceName_subString = 'Name of Device:'
device_ESP32_4Bytes =  '(Esp32Krypto4)'
device_ESP32_8Bytes = '(Esp32Krypto8)'
Unencrypted_Device = 'Unencrypted_device'
decoder_init_subString_time = 'Microseconds elapsed during decoder initialization:'
restore_state_subString_time = 'Microseconds elapsed during decoder restore state:'
MTE_elapse_subString_time = 'Microseconds elapsed during MTE decoding of data:'
MTE_extracted_subString = 'Extracted MTE encoded data:'
decoder_state_save_subString_time = 'Microseconds elapsed during decoder state save:'
Krypto_wb = Workbook() #create an empty excelsheet workbook
Krypto_workbook = xlsxwriter.Workbook('Krypto_MTE_Azure_Logs.xlsx') #use this if using xlsxwriter library
one_ms_to_microseconds = 1000

unencrypted_device_receive_time = 'Microseconds elapsed during recv phase:'

# Start from the first cell.
# Rows and columns are zero indexed.
row = 0
column = 0

Esp32Krypto4_row = 0       # row variable exclusively for 4-Byte device
Esp32Krypto4_column = 0    # column variable exclusively for 4-Byte device

Esp32Krypto8_row = 0       # row variable exclusively for 8-Byte device
Esp32Krypto8_column = 0    # column variable exclusively for 8-Byte device

Unencrypted_device_row = 0      # row variable exclusively for unencrypted device
Unencrypted_device_column = 0   # column variable exclusively for unencrypted device

# Add a bold format to use to highlight cells.
bold = Krypto_workbook.add_format({'bold': True})

# Wrap text in a cell.
cell_format = Krypto_workbook.add_format({'bold': True})
cell_format.set_text_wrap()
cell_format.set_align('vjustify')

Krypto_worksheet_Tx_Rx = Krypto_workbook.add_worksheet("Azure_Tx_to_Rx")
Krypto_worksheet_Decoded_Timing = Krypto_workbook.add_worksheet("Decoded Timing")
Krypto_worksheet_Average_Deltas = Krypto_workbook.add_worksheet("Average Deltas")

Krypto_worksheet_Tx_Rx.write(row + 1, column, "Tx_to_Rx")
Krypto_worksheet_Tx_Rx.write(row, column + 1, device_ESP32_4Bytes + 'Decode Succeed Time(ms) + time_on_air_ms + decoder_state_save_time(ms)', cell_format)
Krypto_worksheet_Tx_Rx.write(row, column + 2, device_ESP32_8Bytes + 'Decode Succeed Time(ms) + time_on_air_ms + decoder_state_save_time(ms)', cell_format)
Krypto_worksheet_Tx_Rx.write(row, column + 3, Unencrypted_Device + 'Decode Succeed Time(ms) + time_on_air_ms + unencrypted_device_receive_time(ms)', cell_format)
Krypto_worksheet_Tx_Rx.write(row, column + 4, device_ESP32_4Bytes + 'Decode Succeed Time(ms) only', cell_format)
Krypto_worksheet_Tx_Rx.write(row, column + 5, device_ESP32_4Bytes + 'time_on_air_ms only', cell_format)
Krypto_worksheet_Tx_Rx.write(row, column + 6, device_ESP32_4Bytes + 'decoder_state_save_time only', cell_format)
Krypto_worksheet_Tx_Rx.write(row, column + 7, device_ESP32_8Bytes + 'Decode Succeed Time(ms) only', cell_format)
Krypto_worksheet_Tx_Rx.write(row, column + 8, device_ESP32_8Bytes + 'time_on_air_ms only', cell_format)
Krypto_worksheet_Tx_Rx.write(row, column + 9, device_ESP32_8Bytes + 'decoder_state_save_time only', cell_format)
Krypto_worksheet_Tx_Rx.write(row, column + 10, Unencrypted_Device + 'Decode Succeed Time(ms) only', cell_format)
Krypto_worksheet_Tx_Rx.write(row, column + 11, Unencrypted_Device + 'time_on_air_ms only', cell_format)
Krypto_worksheet_Tx_Rx.write(row, column + 12, Unencrypted_Device + 'decoder_state_save_time only', cell_format)
Krypto_worksheet_Tx_Rx.write(row, column + 13, device_ESP32_4Bytes + 'Average of (Decode Succeed Time(ms) + time_on_air_ms + decoder_state_save_time(ms))', cell_format)
Krypto_worksheet_Tx_Rx.write(row, column + 14, device_ESP32_8Bytes + 'Average of (Decode Succeed Time(ms) + time_on_air_ms + decoder_state_save_time(ms))', cell_format)
Krypto_worksheet_Tx_Rx.write(row, column + 15, Unencrypted_Device + 'Average of (Decode Succeed Time(ms) + time_on_air_ms + unencrypted_device_receive_time(ms))', cell_format) 

Esp32Krypto4_packet_list = []     # list to keep a track of the values and number of logs per device parsed and to calculate the average etc...
Esp32Krypto8_packet_list = []
Unencrypted_device_packet_list = []



dict_of_flags = {'decode_succeed_time': None, 'packet_received_timestamp':None, 'packet_anchor_start': False, 'packet_anchor_end': False, 'time_on_air_ms': None, 'deviceName': None, 'restore_state_subString_time': None, \
    'restore_state_subString_time': None, 'MTE_elapse_subString_time': None, 'MTE_extracted_subString': None, 'decoder_state_save_subString_time': None}
    
    
unencryped_device_dict_of_flags = {'decode_succeed_time': None, 'packet_received_timestamp':None, 'unencrypted_device_receive_time': None, 'deviceName': None, \
                                   'unencrypted_device_packet_anchor_start': False, 'unencrypted_device_packet_anchor_end': False,'time_on_air_ms': None}

def set_dict_of_flags_defaults():
    #code to set values to original default
    global dict_of_flags # same variable name in this function, hence need to specify whether we are accessing the global one through global keyword.
    dict_of_flags = {'decode_succeed_time': None, 'packet_received_timestamp':None, 'packet_anchor_start': False, 'packet_anchor_end': False, 'time_on_air_ms': None, 'deviceName': None, 'restore_state_subString_time': None, \
        'restore_state_subString_time': None, 'MTE_elapse_subString_time': None, 'MTE_extracted_subString': None, 'decoder_state_save_subString_time': None}
    #print("dictionary of flags set to defaults".format(dict_of_flags))
    

def set_Unencrypted_device_dict_of_flags_defaults():
    global unencryped_device_dict_of_flags
    unencryped_device_dict_of_flags = {'decode_succeed_time': None, 'packet_received_timestamp':None, 'unencrypted_device_receive_time': None,\
                                       'unencrypted_device_packet_anchor_start': False, 'unencrypted_device_packet_anchor_end': False,'time_on_air_ms': None}
        

def calculate_tx_to_rx_ms(updated_dict_of_flags):
    #print(updated_dict_of_flags)
    if(updated_dict_of_flags['deviceName'] == '(Esp32Krypto4)'):
        result = float(updated_dict_of_flags['decode_succeed_time']) + float(updated_dict_of_flags['time_on_air_ms']) \
            + float(updated_dict_of_flags['decoder_state_save_subString_time'])/one_ms_to_microseconds #convert everything to milliseconds and return
        Esp32Krypto4_packet_list.append(result)
        
    if(updated_dict_of_flags['deviceName'] == '(Esp32Krypto8)'):
        result = float(updated_dict_of_flags['decode_succeed_time']) + float(updated_dict_of_flags['time_on_air_ms']) \
            + float(updated_dict_of_flags['decoder_state_save_subString_time'])/one_ms_to_microseconds #convert everything to milliseconds and return
        Esp32Krypto8_packet_list.append(result)
        
    if(updated_dict_of_flags['deviceName'] == 'Unencrypted_device'):
        result = float(unencryped_device_dict_of_flags['decode_succeed_time']) + float(unencryped_device_dict_of_flags['unencrypted_device_receive_time'])\
            + float(unencryped_device_dict_of_flags['time_on_air_ms'])
        Unencrypted_device_packet_list.append(result)
    return result

def average_tx_to_rx_ms(deviceName_str): # function to calcuate the average of all tx_to_rx cells for a device
    global Esp32Krypto4_packet_list
    global Esp32Krypto8_packet_list
    global Unencrypted_device_packet_list
    average_tx_rx_ms = 0
    if(deviceName_str == '(Esp32Krypto4)'):
        average_tx_rx_ms = sum(Esp32Krypto4_packet_list)/len(Esp32Krypto4_packet_list)
    elif(deviceName_str == '(Esp32Krypto8)'):
        average_tx_rx_ms = sum(Esp32Krypto8_packet_list)/len(Esp32Krypto8_packet_list)
    elif(deviceName_str == 'Unencrypted_device'):
        average_tx_rx_ms = sum(Unencrypted_device_packet_list)/len(Unencrypted_device_packet_list)
    return average_tx_rx_ms


def write_to_excel_difference_lists_4_Byte_Unencrypted(list1, list2, row, column):

    if(len(list1) < len(list2)):
        list2_temp = list2[:len(list1)]
        list1_temp = list1
    else:
        list1_temp = list1[:len(list2)]
        list2_temp = list2
    subtracted = list()
    for i in range(len(list1_temp)):
        item = list1_temp[i] - list2_temp[i]
        subtracted.append(item)
    Krypto_worksheet_Decoded_Timing.write(row, column + 1, 'Deltas:' + device_ESP32_4Bytes + ' compared to ' + Unencrypted_Device, cell_format)
    for item in subtracted:
        Krypto_worksheet_Decoded_Timing.write(row + 1, column + 1, item)
        row += 1 #update row, keep column same


def write_to_excel_difference_lists_8_Byte_Unencrypted(list1, list2, row, column):

    if(len(list1) < len(list2)):
        list2_temp = list2[:len(list1)]
        list1_temp = list1
    else:
        list1_temp = list1[:len(list2)]
        list2_temp = list2
    subtracted = list()
    for i in range(len(list1_temp)):
        item = list1_temp[i] - list2_temp[i]
        subtracted.append(item)
    Krypto_worksheet_Decoded_Timing.write(row, column + 1, 'Deltas:' + device_ESP32_8Bytes + ' compared to ' + Unencrypted_Device, cell_format)
    for item in subtracted:
        Krypto_worksheet_Decoded_Timing.write(row + 1, column + 1, item)
        row += 1 #update row, keep column same

def write_to_excel_difference_lists_8_Byte_4_Byte(list1, list2, row, column):

    if(len(list1) < len(list2)):
        list2_temp = list2[:len(list1)]
        list1_temp = list1
    else:
        list1_temp = list1[:len(list2)]
        list2_temp = list2
    subtracted = list()
    for i in range(len(list1_temp)):
        item = list1_temp[i] - list2_temp[i]
        subtracted.append(item)
    Krypto_worksheet_Decoded_Timing.write(row, column + 1, 'Deltas:' + device_ESP32_4Bytes + ' compared to ' + device_ESP32_8Bytes, cell_format)
    for item in subtracted:
        Krypto_worksheet_Decoded_Timing.write(row + 1, column + 1, item)
        row += 1 #update row, keep column same        

# convoluted parsed extraction of tokens using regular expressions aka regex.
# input original empirical logs from Azure with decode function: SECURE(encrypted)/INSECURE(plain unencrypted data)
with open(r"/home/asif/Downloads/log_parser_extractor_xcel_dumper/MS_Azure_Logs/log.txt", 'r') as fp:
    for l_no, line in enumerate(fp):
        # search string
        if information_decode_succeed_time in line:
            decode_succeed_time = re.search(r'Duration=(.*?)ms\)', line).group(1) # extract the number between tokens 'Duration=' and ms.
            dict_of_flags['decode_succeed_time'] = decode_succeed_time
            #print(decode_succeed_time)
            
        if packet_anchor_start in line:
            packet_timestamp = re.sub(rf"(.*?) [Warning] Packet Received:", "", line)
            dict_of_flags['packet_received_timestamp'] = packet_timestamp[0:len(azure_log_timestamp_example)]
            #print(packet_timestamp[0:len(azure_log_timestamp_example)])
            #print('string found in a file')
            #print('Line Number:', l_no)
            #print('Line:', line)
            packet_received_string = re.sub(rf"^.+?{re.escape(packet_anchor_start)}", "", line.rstrip())
            #convert string to json object
            packet_received_json_object = json.loads(packet_received_string)    #convert the received packet's sub-object into json from plain text.
            dict_of_flags['time_on_air_ms'] = float(packet_received_json_object['time_on_air_ms'])
            #check new data type
            #print(type(packet_received_json_object))
            #print(packet_received_json_object)
            #print('dataFrame extracted is ', packet_received_json_object["dataFrame"])
            dict_of_flags['packet_anchor_start'] = packet_anchor_start
            
        if deviceName_subString in line:
            if(device_ESP32_4Bytes == re.sub(rf"^.+?{deviceName_subString}"r'\s+', "", line.rstrip())):
                dict_of_flags['deviceName'] = device_ESP32_4Bytes
            elif(device_ESP32_8Bytes == re.sub(rf"^.+?{deviceName_subString}"r'\s+', "", line.rstrip())):
                dict_of_flags['deviceName'] = device_ESP32_8Bytes
                
        if decoder_init_subString_time in line:
            #print(re.sub(rf"^.+?{decoder_init_subString_time}"r'\s+', "", line.rstrip()))
            dict_of_flags['decoder_init_subString_time'] = re.sub(rf"^.+?{decoder_init_subString_time}"r'\s+', "", line.rstrip())
            
        if restore_state_subString_time in line:
            #print(re.sub(rf"^.+?{restore_state_subString_time}"r'\s+', "", line.rstrip()))
            dict_of_flags['restore_state_subString_time'] = re.sub(rf"^.+?{restore_state_subString_time}"r'\s+', "", line.rstrip())
            
        if MTE_elapse_subString_time in line:
            #print(re.sub(rf"^.+?{MTE_elapse_subString_time}"r'\s+', "", line.rstrip()))
            dict_of_flags['MTE_elapse_subString_time'] = re.sub(rf"^.+?{MTE_elapse_subString_time}"r'\s+', "", line.rstrip())
            
        if MTE_extracted_subString in line:
            #print(re.sub(rf"^.+?{MTE_extracted_subString}"r'\s+', "", line.rstrip()))
            dict_of_flags['MTE_extracted_subString'] = re.sub(rf"^.+?{MTE_extracted_subString}"r'\s+', "", line.rstrip())
            
        if decoder_state_save_subString_time in line:
            #print(re.sub(rf"^.+?{decoder_state_save_subString_time}"r'\s+', "", line.rstrip()))
            dict_of_flags['decoder_state_save_subString_time'] = re.sub(rf"^.+?{decoder_state_save_subString_time}"r'\s+', "", line.rstrip())
            
        
        # if the nearing to the log end for the particular device, mark the ending to confirm parsing of the log set.
        if packet_anchor_end in line:
            #print(packet_anchor_end,format("found in file"))
            #print('Line Number:', l_no)
            #print('Line:', line)
            # don't look for next lines
            dict_of_flags['packet_anchor_end'] = packet_anchor_end

        if((dict_of_flags['decode_succeed_time'] is not None) and (dict_of_flags['packet_anchor_end'] == packet_anchor_end) and (dict_of_flags['deviceName'] == '(Esp32Krypto4)')):
            #code to dump selective data to the excelsheet
            Krypto_worksheet_Tx_Rx.write(Esp32Krypto4_row + 1, Esp32Krypto4_column + 1, calculate_tx_to_rx_ms(dict_of_flags))
            Krypto_worksheet_Tx_Rx.write(Esp32Krypto4_row + 1, Esp32Krypto4_column + 4, dict_of_flags['decode_succeed_time'] , cell_format)
            Krypto_worksheet_Tx_Rx.write(Esp32Krypto4_row + 1, Esp32Krypto4_column + 5, dict_of_flags['time_on_air_ms'] , cell_format)
            Krypto_worksheet_Tx_Rx.write(Esp32Krypto4_row + 1, Esp32Krypto4_column + 6, float(dict_of_flags['decoder_state_save_subString_time'])/one_ms_to_microseconds, cell_format)
            Esp32Krypto4_row += 1
            set_dict_of_flags_defaults() # once dictionary of flags is truly and fully filled, call function to clear it after writing to excel sheet
            # print(average_tx_to_rx_ms('(Esp32Krypto4)'))
            continue
        elif((dict_of_flags['decode_succeed_time'] is not None) and (dict_of_flags['packet_anchor_end'] == packet_anchor_end) and (dict_of_flags['deviceName'] == '(Esp32Krypto8)')):
            Krypto_worksheet_Tx_Rx.write(Esp32Krypto8_row + 1, Esp32Krypto8_column + 2, calculate_tx_to_rx_ms(dict_of_flags))
            Krypto_worksheet_Tx_Rx.write(Esp32Krypto8_row + 1, Esp32Krypto8_column + 7, dict_of_flags['decode_succeed_time'] , cell_format)
            Krypto_worksheet_Tx_Rx.write(Esp32Krypto8_row + 1, Esp32Krypto8_column + 8, dict_of_flags['time_on_air_ms'] , cell_format)
            Krypto_worksheet_Tx_Rx.write(Esp32Krypto8_row + 1, Esp32Krypto8_column + 9, float(dict_of_flags['decoder_state_save_subString_time'])/one_ms_to_microseconds, cell_format)
            Esp32Krypto8_row += 1
            set_dict_of_flags_defaults() # once dictionary of flags is truly and fully filled, call function to clear it after writing to excel sheet
            # print(average_tx_to_rx_ms('(Esp32Krypto8)'))
            continue
        

# now parsing the log file for unencrypted device payloads/uplinks received
with open(r"/home/asif/Downloads/log_parser_extractor_xcel_dumper/MS_Azure_Logs/2022-11-28_unencrypted.txt", 'r') as fp:
    for l_no, line in enumerate(fp):
        
        unencryped_device_dict_of_flags['deviceName'] = Unencrypted_Device
        
        if unencrypted_device_packet_anchor_start in line:
            unencryped_device_dict_of_flags['unencrypted_device_packet_anchor_start'] = re.search(r'Id=(.*?)\)', line).group(1) # treat the occurrence of Id value as the start marker or anchor
            #print(unencryped_device_dict_of_flags['unencrypted_device_packet_anchor_start'])
            
        if information_decode_succeed_time in line:
            decode_succeed_time = re.search(r'Duration=(.*?)ms\)', line).group(1) # extract the number between tokens 'Duration=' and ms.
            unencryped_device_dict_of_flags['decode_succeed_time'] = decode_succeed_time
            #print(decode_succeed_time)
        
        if packet_anchor_start in line:
            packet_timestamp = re.sub(rf"(.*?) [Warning] Packet Received:", "", line)
            unencryped_device_dict_of_flags['packet_received_timestamp'] = packet_timestamp[0:len(azure_log_timestamp_example)]
            #print(packet_timestamp[0:len(azure_log_timestamp_example)])
            #print('string found in a file')
            #print('Line Number:', l_no)
            #print('Line:', line)
            unencrypted_packet_received_string = re.sub(rf"^.+?{re.escape(packet_anchor_start)}", "", line.rstrip())
            #convert string to json object
            unencrypted_packet_received_json_object = json.loads(unencrypted_packet_received_string)    #convert the received packet's sub-object into json from plain text.
            unencryped_device_dict_of_flags['time_on_air_ms'] = float(unencrypted_packet_received_json_object['time_on_air_ms'])
            #check new data type
            #print(type(packet_received_json_object))
            #print(packet_received_json_object)
            #print('dataFrame extracted is ', packet_received_json_object["dataFrame"])
            
        if unencrypted_device_receive_time in line:
            unencryped_device_dict_of_flags['unencrypted_device_receive_time'] = int(re.sub(rf"^.+?{unencrypted_device_receive_time}"r'\s+', "", line.rstrip()))
            #print(unencryped_device_dict_of_flags['unencrypted_device_receive_time'])
        
        if unencrypted_device_packet_anchor_end in line:
            unencryped_device_dict_of_flags['unencrypted_device_packet_anchor_end'] =  re.search(r'Id=(.*?)\,', line).group(1)  # treat the occurrence of Id value as the end marker or anchor
            #print(unencryped_device_dict_of_flags['unencrypted_device_packet_anchor_end'])
            
        if((unencryped_device_dict_of_flags['unencrypted_device_packet_anchor_start'] is not False) and (unencryped_device_dict_of_flags['unencrypted_device_packet_anchor_end'] is not False)): # confirm integrity through start/end parsing anchors/markers
            if(unencryped_device_dict_of_flags['unencrypted_device_packet_anchor_start'] == unencryped_device_dict_of_flags['unencrypted_device_packet_anchor_end']):
                Krypto_worksheet_Tx_Rx.write(Unencrypted_device_row + 1, Unencrypted_device_column + 3, calculate_tx_to_rx_ms(unencryped_device_dict_of_flags))
                Krypto_worksheet_Tx_Rx.write(Unencrypted_device_row + 1, Unencrypted_device_column + 10, unencryped_device_dict_of_flags['decode_succeed_time'])
                Krypto_worksheet_Tx_Rx.write(Unencrypted_device_row + 1, Unencrypted_device_column + 11, unencryped_device_dict_of_flags['time_on_air_ms'])
                Krypto_worksheet_Tx_Rx.write(Unencrypted_device_row + 1, Unencrypted_device_column + 12, float(unencryped_device_dict_of_flags['unencrypted_device_receive_time']/one_ms_to_microseconds))
                Unencrypted_device_row += 1
                set_Unencrypted_device_dict_of_flags_defaults()
                continue


Krypto_worksheet_Tx_Rx.write(row + 1, column + 13, average_tx_to_rx_ms(device_ESP32_4Bytes), cell_format)
Krypto_worksheet_Tx_Rx.write(row + 1, column + 14, average_tx_to_rx_ms(device_ESP32_8Bytes), cell_format)
Krypto_worksheet_Tx_Rx.write(row + 1, column + 15, average_tx_to_rx_ms(Unencrypted_Device), cell_format)


write_to_excel_difference_lists_4_Byte_Unencrypted(Esp32Krypto4_packet_list, Unencrypted_device_packet_list, 0, 0)
write_to_excel_difference_lists_8_Byte_Unencrypted(Esp32Krypto8_packet_list, Unencrypted_device_packet_list, 0, 1)
write_to_excel_difference_lists_8_Byte_4_Byte(Esp32Krypto8_packet_list, Esp32Krypto4_packet_list, 0, 2)



Krypto_workbook.close()   #close the workbook:- saves the data written to excel cells.

            

#print("dataFrames count {}".format(count_dataFrames))

print(all(dict_of_flags))
