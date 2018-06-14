from __future__ import print_function

import datetime
import json
import os
from apiclient.discovery import build
from apiclient.http import MediaFileUpload
from httplib2 import Http
from oauth2client import file, client, tools

FILE_PATH = ''
CLIENT_SECRET_PATH = ''
PROJECT_NAME = ''
SEPARATOR = "_"
ASSEMBLE = "assemble"
GRADLE_COMMAND = "./gradlew "
CLEAN = "clean"

DIR_ANDROID_BUILDS = 'AndroidBuilds'
DRIVE_FILE = "DriveFile"
FILE_CREDENTIALS = 'credentials.json'
SCOPES = 'https://www.googleapis.com/auth/drive'
DATE_TIME_FORMAT = "%Y_%m_%d_%H:%M"
CREATE_BUILD_ENABLED = False


class JsonKey:
    buildType = "build_type"
    projectName = "project_name"
    buildPath = "build_path"
    clientSecretPath = "client_secret_path"
    createBuildEnabled = "create_build_for_me"


# Function defination section ___________________________________

# Function to read DriveFile
def readDriveFile():
    print("Reading DriveFile ...")
    dirPath = os.path.dirname(os.path.realpath(__file__))
    drivePath = dirPath + "/" + DRIVE_FILE
    with open(drivePath) as driveFile:
        jsonData = json.load(driveFile)
        return jsonData


# Function to create a root folder by name AndroidBuilds.
def createRootFolder():
    folder_metadata = {'name': [DIR_ANDROID_BUILDS],
                       'mimeType': 'application/vnd.google-apps.folder'}
    folder = service.files().create(body=folder_metadata, fields='id').execute()
    folderId = folder.get('id')
    print("ROOT DIRECTORY CREATED - " + DIR_ANDROID_BUILDS)
    print('\n')
    return folderId


# Function to create a folder with given folder inside AndroidBuilds directory with given project name.
def createProjectFolder(rootDirectoryId, projectName):
    folder_metadata = {'name': [projectName],
                       'mimeType': 'application/vnd.google-apps.folder',
                       'parents': [rootDirectoryId]}
    folder = service.files().create(body=folder_metadata, fields='id').execute()
    folderId = folder.get('id')
    print('PROJECT DIRECTORY CREATED - ' + projectName)
    print('\n')
    return folderId


# Function to upload a new build in  given folder
def uploadBuild(parentId):
    print('UPLOADING BUILD ...')
    filename, fileExtension = os.path.splitext(FILE_PATH)
    buildName = createBuildName(fileExtension)
    file_metadata = {'name': [buildName], 'parents': [parentId]}
    media = MediaFileUpload(FILE_PATH)
    file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    print('BUILD UPLOADED SUCCESSFULLY')
    print('\n')


# Function to create new build name
def createBuildName(fileExtension):
    time = datetime.datetime.now().strftime(DATE_TIME_FORMAT)
    buildName = PROJECT_NAME + SEPARATOR + BUILD_TYPE + SEPARATOR + time + fileExtension
    print("Build: " + buildName)
    print('\n')
    return buildName


# Function to check if the root directory exists or not.
def isDirectoryPresent(directoryName):
    print("Looking for directory: " + directoryName)
    query = "name = '" + directoryName + "'"
    response = service.files().list(q=query).execute()
    file = response.get('files', [])
    if not file:
        print("Directory: " + directoryName + " - Not Found")
        print('\n')
        return False
    else:
        print("Directory:" + directoryName + " - Found")
        print('\n')
        return True


# Function to check if the root directory exists or not.
def getDirectoryId(directoryName):
    print("Fetching id for directory: " + directoryName)
    query = "name = '" + directoryName + "'"
    response = service.files().list(q=query).execute()
    file = response.get('files', [])
    if not file:
        print("Directory ID: " + "Not Found")
        print('\n')
        return ""
    item = file[0]
    print("Directory ID: " + item["id"])
    print('\n')
    return item["id"]


# ________________________________________________________________


# Setup the Drive v3 API
dirPath = os.path.dirname(os.path.realpath(__file__))
credPath = dirPath + "/" + FILE_CREDENTIALS

store = file.Storage(credPath)
creds = store.get()
if not creds or creds.invalid:
    flow = client.flow_from_clientsecrets(CLIENT_SECRET_PATH, SCOPES)
    creds = tools.run_flow(flow, store)
service = build('drive', 'v3', http=creds.authorize(Http()))

# Read data from DriveFile
jsonDriveFile = readDriveFile()

# Set values
FILE_PATH = jsonDriveFile[JsonKey.buildPath]
CLIENT_SECRET_PATH = jsonDriveFile[JsonKey.clientSecretPath]
PROJECT_NAME = jsonDriveFile[JsonKey.projectName]
BUILD_TYPE = jsonDriveFile[JsonKey.buildType]
CREATE_BUILD_ENABLED = jsonDriveFile[JsonKey.createBuildEnabled]

rootDirectoryId = ""
projectDirectoryId = ""
buildDirectoryId = ""
# Check if the root directory present
if not isDirectoryPresent(DIR_ANDROID_BUILDS):
    # If root directory is not present, create new one
    rootDirectoryId = createRootFolder()
else:
    # Else get the id for existing root directory
    rootDirectoryId = getDirectoryId(DIR_ANDROID_BUILDS)

# Check if the project directory is present
if not isDirectoryPresent(PROJECT_NAME):
    # If project directory is not present, create new one
    projectDirectoryId = createProjectFolder(rootDirectoryId, PROJECT_NAME)
else:
    # Else get the id for existing project directory
    projectDirectoryId = getDirectoryId(PROJECT_NAME)

# Check if the build directory is present
if not isDirectoryPresent(BUILD_TYPE):
    # If build directory is not present, create new one
    buildDirectoryId = createProjectFolder(projectDirectoryId, BUILD_TYPE)
else:
    # Else get the id for existing build directory
    buildDirectoryId = getDirectoryId(BUILD_TYPE)

# Create build
if CREATE_BUILD_ENABLED:
    # Create command to generate build from command line. eg. ./gradlew assembleDebug
    buildCommand = GRADLE_COMMAND + ASSEMBLE + BUILD_TYPE
    print("Creating build, executing command: " + buildCommand)
    os.system(GRADLE_COMMAND + CLEAN)
    os.system(buildCommand)

# Upload the build
uploadBuild(buildDirectoryId)
