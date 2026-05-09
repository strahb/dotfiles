import os
import numpy as np
import soundfile as sf
from beets.plugins import BeetsPlugin
from beets.util import syspath
from beets import ui
from beets.ui import decargs

def get_frequency_ceiling(file_path, threshold_db=-70, samples=10):
    ceilings = []
    
    with sf.SoundFile(file_path) as f:
        total_frames = len(f)
        sample_rate = f.samplerate
        frames_per_sample = sample_rate * 5 
        
        checkpoints = [int(total_frames * (i / (samples + 1))) for i in range(1, samples + 1)]
        
        for start_frame in checkpoints:
            if start_frame + frames_per_sample > total_frames:
                break
                
            f.seek(start_frame)
            data = f.read(frames_per_sample)
            
            if len(data.shape) > 1:
                data = np.mean(data, axis=1)

            fft_data = np.abs(np.fft.rfft(data))
            freqs = np.fft.rfftfreq(len(data), 1/sample_rate)

            max_val = np.max(fft_data)
            if max_val == 0:
                continue 
                
            fft_db = 20 * np.log10(fft_data / max_val)

            active_freqs = freqs[fft_db > threshold_db]
            if len(active_freqs) > 0:
                snippet_ceiling = np.max(active_freqs) / 1000
                ceilings.append(snippet_ceiling)

    if ceilings:
        return max(ceilings)
    return 0


class SpectralCheckPlugin(BeetsPlugin):
    def __init__(self):
        super(SpectralCheckPlugin, self).__init__()
        
        self.config.add({
            'bypass': False
        })
        
        self.register_listener('import_task_created', self.on_import_task_created)

    def on_import_task_created(self, task, session):
        env_bypass = os.environ.get('SPECTRAL_BYPASS', '0') == '1'
        if self.config['bypass'].get(bool) or env_bypass:
            self._log.debug('Bypassed')
            return [task]

        items_to_check = task.items if task.items else [task.item]
        
        transcode_found = False
        failed_file = ""

        for item in items_to_check:
            if item.format != 'FLAC':
                continue
                
            file_path = os.fsdecode(item.path)
            self._log.info('Scanning: {0}', os.path.basename(file_path))
            
            try:
                ceiling = get_frequency_ceiling(file_path)
                item['spectral_ceiling'] = round(ceiling, 2)
                
                if ceiling < 19.5:
                    item['is_transcode'] = True
                    transcode_found = True
                    failed_file = f"{os.path.basename(file_path)} [{ceiling:.2f} kHz]"
                    break
                else:
                    item['is_transcode'] = False
                    
            except Exception as e:
                self._log.error('Error: {0}: {1}', item.path, e)
        
        if transcode_found:
            self._log.warning('REJECTED: {0}', failed_file)
            self._log.warning('Bypass: SPECTRAL_BYPASS=1 beet import')
            return []
            
        self._log.info('OK')
        return [task]

    def commands(self):
        cmd = ui.Subcommand('spectral', help='Run spectral analysis on existing FLAC files')
        cmd.parser.add_option('-f', '--force', action='store_true', default=False,
                              help='Re-analyze files even if they already have a spectral_ceiling')
        
        def func(lib, opts, args):
            query = decargs(args) + ['format:FLAC']
            items = lib.items(query)
            
            if not opts.force:
                items = [item for item in items if not item.get('spectral_ceiling')]
                
            total = len(items)
            if total == 0:
                self._log.info("None found. Use -f to force.")
                return

            self._log.info(f"Scanning {total} tracks.")
            
            for i, item in enumerate(items, 1):
                file_path = os.fsdecode(item.path)
                
                try:
                    ceiling = get_frequency_ceiling(file_path)
                    item['spectral_ceiling'] = round(ceiling, 2)
                    
                    if ceiling < 19.5:
                        item['is_transcode'] = True
                        self._log.warning(f"[{i}/{total}] FAIL [{ceiling:.2f} kHz]: {item.artist} - {item.title}")
                    else:
                        item['is_transcode'] = False
                        self._log.info(f"[{i}/{total}] PASS [{ceiling:.2f} kHz]: {item.artist} - {item.title}")
                        
                    item.store()
                    
                except Exception as e:
                    self._log.error(f"[{i}/{total}] ERROR [{os.path.basename(file_path)}]: {e}")
                    
        cmd.func = func
        return [cmd]