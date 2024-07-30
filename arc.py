from datetime import datetime
from fastkml import kml
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon
import requests
import csv

def csvCheck():
    kml_file_path = 'CityCouncilMapper/PortlandCityCouncilDistricts.kml'
    
    #Build the districts fomr the kml file
    districts = {}   
    with open(kml_file_path, 'rb') as f:
        k = kml.KML()
        k.from_string(f.read())

    for doc in list(k.features()):
        for folder in list(doc.features()):
            for placemark in list(folder.features()):
                coordinates = [(coord[0], coord[1]) for coord in placemark.geometry.exterior.coords]
                districts[placemark.name] = Polygon(coordinates)

    csv_file_path = ''
    knownAddresses = {}
    manualExit = False
    with open(csv_file_path, 'r', newline='') as csvfile:
        reader = csv.reader(csvfile)
        rows = list(reader)
        for i, row in enumerate(rows, 0):
            if i == 0:
                continue
            # sanity check/debugging out
            if ('D' in row[15] or manualExit):
                writeCSV(csv_file_path, rows)
                break
            
            #check if this is an apartment and try to get just the address
            row_addr = row[1].lower()  
            for aptTerm in ['unit', 'apt', '#', 'rm']:
                if aptTerm in row_addr:
                    row_addr = row_addr.split(aptTerm)[0].rstrip(' ')
                    break

            if row_addr in knownAddresses:
                row[15] = knownAddresses[row_addr]
                continue

            addr = row_addr + ', Portland, ME'
            response = requests.get('https://maps.googleapis.com/maps/api/geocode/json', params={'address': addr, 'key': ''})
            data = response.json()
            location = data['results'][0]['geometry']['location']
            point = Point(location['lng'], location['lat'])
            
            for district, polygon in districts.items():    
                if polygon.contains(point):
                    row[15] = district
                    knownAddresses[row_addr] = district
                    break
    
            print(f"{i}/{len(rows)} + {row[15]}")
    
    writeCSV(csv_file_path, rows)
    
def writeCSV(csv_file_path, rows):
    # Write the updated rows back to the CSV file
    with open(csv_file_path + datetime.now().strftime("%m%d%y%H%M"), 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(rows)
    
csvCheck()