from commonfunctions import *
from Colorization.GAN import colorization


def getVideoFrames(FileName):
    """This function return all the video or clip frames """
    print("[INFO] starting video stream...")
    cap = cv.VideoCapture(FileName)
    hasFrame, frame = cap.read()
    VideoFrames = []
    while hasFrame:
        VideoFrames.append(frame)
        hasFrame, frame = cap.read()
    print("[INFO] video stream...done")
    return VideoFrames


def WriteFrames(FileName, image, ShootNum):
    """This function return all the video or clip frames """
    filename = 'Input_and_Output/Shoot#' + str(ShootNum) + '/' + str(FileName) + '.Frame.png'
    # Convert from BGR to RGB
    image = image[:, :, ::-1]
    # Write Frame
    cv2.imwrite(filename, image)
    print("[INFO] Frame" + str(FileName) + " has been written...done")


def WriteImage(image):
    """This function return all the video or clip frames """
    filename = 'Input_and_Output/' + "ColorizedImage" + '.png'
    cv2.imwrite(filename, image[:, :, ::-1])
    print("[INFO] Image has been written...done")


def getFrameShoots(frameList, Threshold, showSteps=False, HistogramThreshold=60):
    """
    input:  Movie Frame List,The Threshold needed for cutting into shots
    output: frames for each shoot
    function: takes a clip and cut it into shoots based on the grayscale and absolute sum difference
    """
    print("[INFO] starting shots detection..")
    preDifference = 0
    shootList = []
    shootFrames = []
    TotalPixelNum = frameList[0].shape[0] * frameList[0].shape[1]
    for i in range(len(frameList) - 1):
        shootFrames.append(frameList[i])
        # Get the Sum of absolute differences of each consecutive frame
        pixelDifference = np.sum(abs(rgb2gray(frameList[i + 1]) - rgb2gray(frameList[i])))
        # Normalization of SAD
        # pixelDifference /= TotalPixelNum

        histogramDifference = getHistoDiff(rgb2gray(frameList[i]), rgb2gray(frameList[i + 1]))
        shootDet = abs(pixelDifference - preDifference)
        if showSteps:
            print("Sad Threshold:", pixelDifference, shootDet, "HistogramThreshold", histogramDifference)
        if shootDet > Threshold and len(
                shootFrames) > 45 and (histogramDifference > HistogramThreshold):  # avoid catching too many transition
            if showSteps:
                show_images([shootFrames[0][:, :, ::-1], shootFrames[-1][:, :, ::-1]], ["Start", "End"])
            shootList.append(shootFrames)
            # reset the shootFrames
            shootFrames = []
        preDifference = pixelDifference
    if len(shootList) == 0:
        print("[INFO] no shoot detection for this video, tune the threshold")
        shootList = [frameList]
        shootFrames = []

    if len(shootFrames) != 0:
        shootList.append(shootFrames)  # to append last frames after the last end of last shoot
    print("[INFO] Shoot Detection .. done Total #Shots is ", len(shootList))
    return shootList


def getHistoDiff(Frame, NextFrame, showSteps=False):
    Frame = Frame.astype("uint8")
    NextFrame = NextFrame.astype("uint8")
    histCurr = cv2.calcHist([Frame], [0], None, [256], [0, 256])
    histNext = cv2.calcHist([NextFrame], [0], None, [256], [0, 256])
    Diff = np.sum(abs(histCurr - histNext))
    return Diff


def getKeyFrame(rShoot):
    """
        input:  Frame shoots
        output: the MI Frame : contains most of the contours
        function: return the maximum frame with contours
    """
    MaxContourNumber = 0
    KeyFrame = rShoot[0]
    indexKeyFrame = 0
    for i in range(len(rShoot)):
        gk = (rgb2gray(rShoot[i]) * 255).astype("uint8")
        _, gk = cv2.threshold(gk, 200, 255, cv2.THRESH_BINARY)
        # Get Image Contours
        contours_gk, _ = cv2.findContours(gk, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)  # for current frame
        if len(contours_gk) > MaxContourNumber:
            KeyFrame = rShoot[i]
            indexKeyFrame = i
            MaxContourNumber = len(contours_gk)
    print("INFO : get KeyFrame in shoot is Done .. ")
    return KeyFrame, indexKeyFrame


def getKeyFrame(rShoot, genModel, Type=0):
    """
        input:  Frame shoots , generator model ,
        type 0=> get the frame with the maximum number of contour in
        type 1 => get the frame with the maximum colorized pixels
        output: the MI Frame : contains most of the colors
        function: return the maximum frame with contours
    """
    maxNum_pixelColorized = 0
    KeyFrame = rShoot[0]
    indexKeyFrame = 0
    if Type:
        for i in range(len(rShoot)):
            # Colorize the frame
            ColorizedFrame = colorization(rShoot[i], genModel)
            # Convert from rgb to lab
            lab_Frame = color.rgb2lab(ColorizedFrame)
            # Count the a & b channels
            CurrentColorizedPixelSum = np.sum(lab_Frame[:, :, 1] != 0) + np.sum(lab_Frame[:, :, 2] != 0)
            if CurrentColorizedPixelSum > maxNum_pixelColorized:
                KeyFrame = rShoot[i]
                indexKeyFrame = i
                maxNum_pixelColorized = CurrentColorizedPixelSum
    else:
        MaxContourNumber = 0
        KeyFrame = rShoot[0]
        indexKeyFrame = 0
        for i in range(len(rShoot)):
            gk = (rgb2gray(rShoot[i]) * 255).astype("uint8")
            _, gk = cv2.threshold(gk, 200, 255, cv2.THRESH_BINARY)
            # Get Image Contours
            _,contours_gk, _ = cv2.findContours(gk, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)  # for current frame
            if len(contours_gk) > MaxContourNumber:
                KeyFrame = rShoot[i]
                indexKeyFrame = i
                MaxContourNumber = len(contours_gk)
    print("[INFO] : get KeyFrame in shoot is Done .. ")
    return KeyFrame, indexKeyFrame


def FramesToVideo(dirr):
    img_array = []
    size = 0
    for filename in sorted(glob.glob(dirr)):
        print(filename)
        img = cv2.imread(filename)
        height, width, layers = img.shape
        size = (width, height)
        img_array.append(img)

    out = cv2.VideoWriter('Input_and_Output/OutputVideo.avi', cv2.VideoWriter_fourcc(*'DIVX'), 15, size)

    for i in range(len(img_array)):
        out.write(img_array[i])
    out.release()


def WriteMovieFrames(MovieFrames, MovieName):
    height, width, layers = MovieFrames[0].shape
    size = (width, height)
    out = cv2.VideoWriter(MovieName + ".avi", cv2.VideoWriter_fourcc(*'DIVX'), 24, size)
    for i in range(len(MovieFrames)):
        MovieFrames[i] = cv2.cvtColor(MovieFrames[i], cv2.COLOR_BGR2RGB)
        out.write(MovieFrames[i])
    out.release()


def IntegrateAudio(Videopath, MovieName):
    """
        input:  B&W Video Path , MovieName after colorized
        output: Integrate B&W audio with colorized video
        function: Integrate the video audio with the colorized frame
    """
    # Read B&W Video
    video = moviepy.editor.VideoFileClip(Videopath)
    audio = video.audio
    # Create the audio file
    audio.write_audiofile("Input_and_Output/sample.mp3")
    # Read Colorized Video
    my_clip = moviepy.editor.VideoFileClip(MovieName + ".avi")
    # Read audio of B&W
    final_audio = moviepy.editor.AudioFileClip('Input_and_Output/sample.mp3')
    # Integrate both of them
    final_clip = my_clip.set_audio(final_audio)
    # Write the output
    final_clip.write_videofile("Input_and_Output/LastOutput.mp4")
    print("[INFO] Integration is Done")
def Video2Gray(FrameList):
    height, width, layers = FrameList[0].shape
    size = (width, height)
    out = cv2.VideoWriter("GrayScale" + ".avi", cv2.VideoWriter_fourcc(*'DIVX'), 24, size)
    for i in range(len(FrameList)):
        FrameList[i] = cv2.cvtColor(FrameList[i], cv2.COLOR_BGR2GRAY)
        out.write(FrameList[i])
    out.release()