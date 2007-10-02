import os.path

extensionToMimeType = {'html':'text/html',
                       'xml':'text/xml',
                       'js':'pplication/x-javascript',
                       'css':'text/css',
                       'gif':'image/gif',
                       'png':'image/png',
                       'jpg':'image/jpeg',
                       }


def directoryClassOutput(callingFile, outputOptions):
    path = outputOptions['location']
    for item in path:
        assert item != '..'

    ext = os.path.splitext(path[-1])[1][1:]
    file = open(os.path.join(os.path.splitext(callingFile)[0] + '.scripts',
                             *path))
    try:
        return {Webwidgets.Constants.FINAL_OUTPUT: file.read(),
                'Content-type': extensionToMimeType[ext]}
    finally:
        file.close()
