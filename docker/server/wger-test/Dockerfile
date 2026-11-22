FROM wger/server:2.7@sha256:1c5789b93bfe5eed0b7287255782d9177027b255de2b22b59f511a693a48db04
COPY --chown=wger:wger aurora_settings.py aurora_sso.py init.py import_data.py import_values.py report.py /home/wger/src/
COPY --chown=wger:wger start.sh /home/wger/aurora-start.sh
CMD ["bash", "/home/wger/aurora-start.sh"]
