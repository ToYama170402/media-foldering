from ffmpeg import probe
import exifread
import datetime
import pathlib
import shutil
import filecmp
import json


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
            MetaData = probe(VideoPath)
            DateTime = MetaData.get("format").get("tags").get("creation_time")
        except:
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
            MediaDateTime = ImageDateTime(MediaPath)
        elif VideoDateTime(MediaPath) != None:
            MediaDateTime = VideoDateTime(MediaPath)
        else:
            return None
        print(f"{MediaPath} : {MediaDateTime}")
        return MediaDateTime


def MoveMedia(Directory: pathlib, File: pathlib, RenamePattern: str):
    """指定されたディレクトリに指定されたファイルをリネームして移動

    Args:
        Directory (pathlib): 移動先ディレクトリを指定
        File (pathlib): 移動するファイルを指定
        RenamePattern(str):リネームのパターン
    """
    if File.is_file():
        if CreationTime(File) == None:
            Num = 0
            while True:
                MovePath = Directory / \
                    f"No EXIF/{File.stem} {Num:03}{File.suffix}"
                if not MovePath.exists():
                    break
                else:
                    Num += 1
        elif CreationTime(File) != None:
            MediaTime = CreationTime(File)
            Num = 0
            while True:
                MovePath = Directory / \
                    f"{MediaTime:{RenamePattern}} {Num:03}{File.suffix}"
                if not MovePath.exists():
                    break
                else:
                    Num += 1
        print(f"{File} to {MovePath}")
        MovePath.parent.mkdir(parents=True, exist_ok=True)
        File.rename(MovePath)


def FindDuplicatedFile(File: pathlib, Directory: pathlib) -> bool:
    """指定されたディレクトリに指定されたファイルと同等のものがあるか判断

    Args:
        File (pathlib): 同一ファイルの存在を確認したいファイルを指定
        Directories (pathlib): 確認先のディレクトリを指定

    Returns:
        bool: 同一ファイルが存在すればTrue、なければFalse
    """
    if File.is_file() and Directory.is_dir:
        Ext = File.suffix
        for CompFile in Directory.glob(f"**/*{Ext}"):
            if filecmp.cmp(File, CompFile, False) and File != CompFile:
                print(f"{File} = {CompFile}")
                return True
        return False


if __name__ == "__main__":
    with open("setting.json", "r", encoding="utf-8")as SettingFile:
        Setting = json.load(SettingFile)
    InputDir = pathlib.Path(Setting["InputDir"])
    OutputDir = pathlib.Path(Setting["OutputDir"])
    NamePattern = Setting["NamePattern"]
    if InputDir.is_dir() and OutputDir.is_dir():
        for MediaFile in InputDir.glob(pattern="**/*"):
            if MediaFile.is_file() and not FindDuplicatedFile(MediaFile, OutputDir):
                MoveMedia(OutputDir, MediaFile, NamePattern)
