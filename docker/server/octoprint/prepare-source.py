import pathlib,zipfile
archive=pathlib.Path('/tmp/aurora-plugins/costestimation.zip')
with zipfile.ZipFile(archive) as source:
    root=source.namelist()[0].split('/')[0]
    static=root+'/octoprint_costestimation/_static_version.py'
    target=archive.with_suffix('.fixed.zip')
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as out:
        for info in source.infolist():
            if info.filename!=static: out.writestr(info,source.read(info.filename))
        out.writestr(static,pathlib.Path('/tmp/costestimation-static.py').read_bytes())
target.replace(archive)
