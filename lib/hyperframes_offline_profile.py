"""Explicit child-process settings for an already prepared local runtime."""
import os
from pathlib import Path


def environment(profile, network_log):
    paths = {name: Path(profile[name]).resolve() for name in
             ('node', 'browser', 'package_dir', 'scratch')}
    for name in ('node', 'browser'):
        if not paths[name].is_file():
            raise ValueError('Missing prepared ' + name)
    if not (paths['package_dir'] / 'package.json').is_file():
        raise ValueError('Missing prepared HyperFrames package')
    guard = Path(__file__).resolve().parents[1] / 'scripts/hyperframes_network_guard.cjs'
    env = dict(os.environ)
    env.update(
        PATH=str(paths['node'].parent) + os.pathsep + env.get('PATH', ''),
        HYPERFRAMES_PACKAGE_DIR=str(paths['package_dir']),
        HYPERFRAMES_BROWSER_PATH=str(paths['browser']),
        HYPERFRAMES_CACHE_DIR=str(paths['scratch'] / 'cache'),
        HYPERFRAMES_EXTRACT_CACHE_DIR=str(paths['scratch'] / 'extract'),
        HYPERFRAMES_CONFIG_DIR=str(paths['scratch'] / 'config'),
        HYPERFRAMES_NO_UPDATE_CHECK='1', HYPERFRAMES_NO_AUTO_INSTALL='1',
        HYPERFRAMES_SKIP_SKILLS='1', HYPERFRAMES_NO_TELEMETRY='1',
        DO_NOT_TRACK='1', NODE_DISABLE_COMPILE_CACHE='1', CI='1',
        PUPPETEER_SKIP_DOWNLOAD='1',
        NODE_OPTIONS='--require="' + str(guard) + '"',
        OPENMONTAGE_HF_NETWORK_LOG=str(Path(network_log).resolve()),
    )
    # The prepared npm layout contains GSAP beside HyperFrames. An explicit
    # override supports a different prepared layout; missing resources fail at scaffold.
    gsap = Path(profile['gsap_package_dir']) if profile.get('gsap_package_dir') else paths['package_dir'].parent / 'gsap'
    env['HYPERFRAMES_GSAP_PACKAGE_DIR'] = str(gsap.resolve())
    return env
