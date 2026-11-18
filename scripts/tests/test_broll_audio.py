import array
import html as html_lib
import re
import math
import hashlib
import json
import tempfile
import unittest
import wave
from pathlib import Path
from scripts.composer.broll_audio import settings, markup
from scripts.core import oslib, editlib, reviewlib

class BrollAudioTests(unittest.TestCase):
    def test_settings(self):
        c = {'in': 0, 'out': .1, 'audio': {'enabled': True}}
        v = settings(c)
        self.assertAlmostEqual(v['fade_in']+v['fade_out'], .1)
        for patch in ({'gain_db': float('nan')}, {'duck_db': 1}, {'gain_db': True},
                      {'fade_out': .2}, {'enabled': 'yes'}, {'offset': 2}):
            with self.assertRaises(ValueError):
                settings({**c, 'audio': patch})

    def test_extraction_cache_and_fingerprints(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td); hf = p/'hf'; hf.mkdir(); (hf/'index.html').write_text('test')
            src = p/'source.wav'
            oslib.run([oslib.FFMPEG,'-v','error','-f','lavfi','-i',
                       'aevalsrc=if(lt(t\\,2)\\,0\\,0.3*sin(2*PI*440*t)):s=48000:d=9',str(src)])
            before = hashlib.sha256(src.read_bytes()).hexdigest()
            media = {'s': {'file':'source.wav'}}
            c = {'id':'a','source':'s','in':3,'out':9,'source_in':1,
                 'audio':{'enabled':True,'fade_in':0,'fade_out':1}}
            sb = {'broll':[c]}; caps = {'words':[{'start':5,'end':6}]}
            html = markup(p,sb,media,caps,hf)
            self.assertIn('data-start="3"',html)
            self.assertIn('data-duration="6"',html)
            f = next((hf/'assets/broll-audio').glob('*.wav'))
            with wave.open(str(f)) as w:
                self.assertEqual(w.getnframes(),288000)
                self.assertEqual(w.getframerate(),48000)
                self.assertEqual(w.getnchannels(),2)
                self.assertEqual(set(w.readframes(48000)),{0})
            with wave.open(str(f)) as w:
                samples = array.array('h', w.readframes(w.getnframes()))
            def rms(xs):
                return math.sqrt(sum(x*x for x in xs)/len(xs))
            self.assertLess(rms(samples[-9600:]), rms(samples[192000:201600])*.15)
            auto = json.loads(html_lib.unescape(re.search(r'data-automation="([^"]+)"', html).group(1)))
            points = auto['lanes'][0]['points']
            self.assertTrue(any(x['t'] == 2 and abs(x['v']-10**(-12/20)) < 1e-8 for x in points))
            # Source starts sounding at 2 s; extraction starts at 1 s: sound stays at local 1 s.
            self.assertGreater(rms(samples[96000:105600]), 1000)
            stamp=f.stat().st_mtime_ns
            self.assertEqual(markup(p,sb,media,caps,hf),html)
            self.assertEqual(stamp,f.stat().st_mtime_ns)
            (p/'storyboard.json').write_text('{}')
            review = reviewlib.fingerprint(p, 'B')
            fp=editlib.hf_fingerprint(p); platform=editlib.platform_fingerprint(p,'tiktok')
            data=bytearray(f.read_bytes());data[-100]^=1;f.write_bytes(data)
            self.assertNotEqual(review, reviewlib.fingerprint(p, 'B'))
            self.assertNotEqual(fp,editlib.hf_fingerprint(p))
            self.assertNotEqual(platform,editlib.platform_fingerprint(p,'tiktok'))
            sb['broll'].append({**c,'id':'b','in':10,'out':15,'source_in':3})
            self.assertEqual(markup(p,sb,media,caps,hf).count('<audio'),2)
            self.assertEqual(hashlib.sha256(src.read_bytes()).hexdigest(),before)
            c['source_in']=8
            with self.assertRaisesRegex(ValueError,'insuficiente'):
                markup(p,sb,media,caps,hf)
            self.assertEqual(markup(p,{'broll':[{'in':0,'out':1}]},media,caps,hf),'')
            self.assertFalse(list((hf/'assets/broll-audio').glob('*.wav')))

    def test_no_audio(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)
            oslib.run([oslib.FFMPEG,'-v','error','-f','lavfi','-i','color=s=32x32:d=1','-an',str(p/'silent.mp4')])
            with self.assertRaisesRegex(ValueError,'sin audio'):
                markup(p,{'broll':[{'id':'a','source':'s','in':0,'out':1,'audio':{'enabled':True}}]},
                       {'s':{'file':'silent.mp4'}},{'words':[]},p/'hf')

    def test_render_sound_and_picture_share_timeline(self):
        import subprocess
        import shutil
        with tempfile.TemporaryDirectory() as td:
            p=Path(td); hf=p/'hf'; (hf/'assets').mkdir(parents=True)
            src=p/'source.mp4'
            oslib.run([oslib.FFMPEG,'-v','error','-f','lavfi','-i',
                       "color=black:s=64x64:r=30:d=4,drawbox=color=white:t=fill:enable='gte(t,2)'",
                       '-f','lavfi','-i','aevalsrc=if(lt(t\\,2)\\,0\\,0.3*sin(2*PI*440*t)):s=48000:d=4',
                       '-c:v','libx264','-c:a','aac',str(src)])
            shutil.copy(src,hf/'assets/source.mp4')
            clip={'id':'sync','source':'s','in':1,'out':4,'source_in':1,
                  'audio':{'enabled':True,'gain_db':0,'duck_db':0,'fade_in':0,'fade_out':0}}
            audio=markup(p,{'broll':[clip]},{'s':{'file':'source.mp4'}},{'words':[]},hf)
            root=Path(__file__).resolve().parents[2]
            shutil.copy(root/'node_modules/gsap/dist/gsap.min.js',hf/'assets/gsap.js')
            (hf/'index.html').write_text('<html><head><script src="assets/gsap.js"></script></head><body style="margin:0;background:black">'
                '<div data-composition-id="main" data-start="0" data-duration="4" data-width="64" data-height="64">'
                '<video class="clip" src="assets/source.mp4" muted playsinline data-start="1" data-duration="3" '
                'data-media-start="1" style="width:64px;height:64px"></video>'+audio+'</div>'
                '<script>window.__timelines["main"]=gsap.timeline({paused:true});</script></body></html>')
            render_log = p/'render.log'
            print(f'Render de sincronía: {render_log}', flush=True)
            with render_log.open('w') as log:
                result=subprocess.run([str(root/'node_modules/.bin/hyperframes'),'render','-q','draft','--sdr','-o','out.mp4'],
                                      cwd=hf,stdout=log,stderr=subprocess.STDOUT,timeout=600)
            self.assertEqual(result.returncode,0,render_log.read_text()[-3000:])
            def decode(args):
                return subprocess.check_output([oslib.FFMPEG,'-v','error','-i',str(hf/'out.mp4'),*args])
            audio=array.array('h',decode(['-vn','-ac','1','-ar','48000','-f','s16le','-']))
            frames=decode(['-an','-vf','scale=1:1','-pix_fmt','gray','-f','rawvideo','-'])
            visual=next(i/30 for i,x in enumerate(frames) if x>180)
            audible=next(i/48000 for i in range(0,len(audio),480) if max(abs(x) for x in audio[i:i+480])>1000)
            self.assertLessEqual(abs(visual-audible),1/30)
