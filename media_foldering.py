from ffmpeg import probe
import exifread
import datetime
import pathlib
import filecmp


def ImageDateTime(ImagePath: pathlib) -> datetime.datetime:
    """指定された画像ファイルの撮影日時を取得

    Args:
        ImagePath (pathlib): 撮影日時を取得したいファイルを指定

    Returns:
        datetime.datetime: Exifの撮影日時に該当するものを返す
    """
    if ImagePath.is_file and ImagePath.exists():
        with open(ImagePath, "rb") as ImageFile:
            try:
                tags = exifread.process_file(ImageFile)
            except:
                return None
        if "EXIF DateTimeOriginal" in tags.keys():
            DateTimeOriginal = tags["EXIF DateTimeOriginal"]
        elif "EXIF DateTimeDigitize" in tags.keys():
            DateTimeOriginal = tags["EXIF DateTimeDigitize"]
        elif "Image DateTime" in tags.keys():
            DateTimeOriginal = tags["Image DateTime"]
        else:
            return None  # 日付データがなければNoneを返す
        if DateTimeOriginal != None:
            try:
                CreationTime = datetime.datetime.strptime(
                    str(DateTimeOriginal), "%Y:%m:%d %H:%M:%S")
            except ValueError:
                return None
            return CreationTime
    else:
        return None


def VideoDateTime(VideoPath: pathlib) -> datetime.datetime:
    """指定された動画ファイルの撮影日時を取得

    Args:
        VideoPath (pathlib):撮影日時を取得したい動画ファイルを指定

    Returns:
        datetime.datetime: 撮影日時に該当する日付を返す
    """
    if VideoPath.is_file:
        MetaData = probe(VideoPath)
        try:
            DateTime = MetaData.get("format").get("tags").get("creation_time")
        except AttributeError:  # 日付データがなければNoneを返す
            return None
        if DateTime == None:
            return None
        else:
            CreationTime = datetime.datetime.strptime(
                DateTime, "%Y-%m-%dT%H:%M:%S.%f%z")
            LocalCreationTime = CreationTime.astimezone()
            return LocalCreationTime
    else:
        return None


def CreationTime(MediaPath: pathlib) -> datetime.datetime:
    """ImageDateTime()とVideoDateTime()のどちらか機能する方を返す

    Args:
        MediaPath (pathlib): 撮影日時を取得したい画像・動画ファイルを指定

    Returns:
        datetime.datetime: 撮影日時に該当する日付を返す
    """
    if MediaPath.is_file:
        if ImageDateTime(MediaPath) != None:
            return ImageDateTime(MediaPath)
        elif VideoDateTime(MediaPath) != None:
            return VideoDateTime(MediaPath)
        else:
            return None


def GeneratePath(Directory: pathlib, File: pathlib, MediaTime: datetime, Num: int) -> pathlib:
    """指定ディレクトリ/年/月/日/年-月-日 時-分 ゼロ埋め三桁整数.拡張子 のパスを生成

    Args:
        Directory (pathlib): ディレクトリを指定
        File (pathlib): 画像・動画ファイルを指定
        MediaTime (datetime): 画像・動画ファイルの撮影日時を指定
        Num (int): ファイル名末尾につける数字を指定

    Returns:
        pathlib: 生成したファイルパスを返す
    """
    MovePath = Directory / \
        f"{MediaTime:%Y/%m/%d/%Y-%m-%d %H-%M} {Num:03}{File.suffix}"
    return MovePath


def MoveMedia(Directory: pathlib, File: pathlib):
    """指定されたディレクトリに指定されたファイルをリネームして移動

    Args:
        Directory (pathlib): 移動先ディレクトリを指定
        File (pathlib): 移動するファイルを指定
    """
    if File.is_file():
        MediaTime = CreationTime(File)
        num = 0
        MovePath = GeneratePath(Directory, File, MediaTime, num)
        while MovePath.exists():
            num += 1
            MovePath = GeneratePath(Directory, File, MediaTime, num)
        MovePath.parent.mkdir(parents=True, exist_ok=True)
        File.rename(MovePath)


def FindDuplicatedFile(File: pathlib, Directory: pathlib) -> bool:
    """指定されたディレクトリに指定されたファイルと同等のものがあるか判断

    Args:
        File (pathlib): 同一ファイルの存在を確認したいファイルを指定
        Directory (pathlib): 確認先のディレクトリを指定

    Returns:
        bool: 同一ファイルが存在すればTrue、なければFalse
    """
    if File.is_file() and Directory.is_dir:
        Ext = File.suffix
        for CompFile in Directory.glob(f"**/*{Ext}"):
            if filecmp.cmp(File, CompFile):
                return True
            else:
                return False
