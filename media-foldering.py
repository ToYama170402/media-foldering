import os
from ffmpeg import probe
import exifread
import datetime
import pathlib


# ファイルパスと撮影日時を保持するクラス
class Media:
    def __init__(self, FilePath: pathlib.Path, Date: datetime.datetime):
        self.FilePath = pathlib.Path(FilePath)
        self.Date = Date


# 指定ディレクトリの中をファイルを再帰的に探索する関数
# pathlib.pathのリストを返す
def FindFileDirectory(Directory: str, FileExts: list) -> list:
    DirectoryPath = pathlib.Path(Directory)
    if DirectoryPath.is_dir() and DirectoryPath.exists():
        FilePathList = []
        for CurrentDirectory, Directories, Files in os.walk(Directory):
            for File in Files:
                FilePath = pathlib.Path(CurrentDirectory, File)
                ext = FilePath.suffix
                for FileExt in FileExts:
                    if ext.casefold() == FileExt.casefold():
                        FilePathList.append(FilePath)
        return FilePathList
    else:
        return None


# 指定された画像ファイルの撮影日時を取得
def ImageDateTime(ImagePath: pathlib) -> datetime.datetime:
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


# 指定された動画ファイルの撮影日時を取得
def VideoDateTime(VideoPath: pathlib) -> datetime.datetime:
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


# ImageDateTimeとVideoDateTimeのどちらか機能する方を返す
def CreationTime(MediaPath: pathlib) -> datetime.datetime:
    if MediaPath.is_file:
        if ImageDateTime(MediaPath) != None:
            return ImageDateTime(MediaPath)
        elif VideoDateTime(MediaPath) != None:
            return VideoDateTime(MediaPath)
        else:
            return None


# 指定ディレクトリ/年/月/日/年-月-日 時-分 ゼロ埋め三桁整数.拡張子 のパスを生成
def GeneratePath(Directory: pathlib, File: pathlib, MediaTime: datetime, Num: int) -> pathlib:
    MovePath = Directory / \
        f"{MediaTime:%Y/%m/%d/%Y-%m-%d %H-%M} {Num:03}{File.suffix}"
    return MovePath


# 指定されたディレクトリに指定されたファイルをリネームして移動
def MoveMedia(Directory: pathlib, File: pathlib):
    if File.is_file():
        MediaTime = CreationTime(File)
        num = 0
        MovePath = GeneratePath(Directory, File, MediaTime, num)
        while MovePath.exists():
            num += 1
            MovePath = GeneratePath(Directory, File, MediaTime, num)
        MovePath.parent.mkdir(parents=True, exist_ok=True)
        File.rename(MovePath)
    else:
        return None
