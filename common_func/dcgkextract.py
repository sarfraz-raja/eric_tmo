import copy
import tempfile
import os
import shutil
import gzip
from zipfile import ZipFile
from common_func.dcgkparse import parse_file


class dcgkextract:
    def __init__(self, inzip=''):
        self.inzip = inzip
        self.dir_source = {}
        self.log_dirs = None if self.inzip is None or len(self.inzip) == 0 else self.extract_all_zip(self.inzip)
        self.mom_files = {}
        self.source_files = {}
        self.merged_dict = self.process_dcgk_files_to_dict()

    def get_unzipped_dirs(self):
        return self.extract_all_zip(self.inzip)

    def extract_all_zip(self, inzip):
        outdir = self.extract_dir(inzip)
        for zipdir in outdir:
            for infile in os.listdir(zipdir):
                if 'dcg_k.log.gz' in infile: self.gunzip_shutil(os.path.join(zipdir, infile))
                if '_showall.log.gz' in infile: self.gunzip_shutil(os.path.join(zipdir, infile))
        return outdir

    def extract_dir(self, inzip):
        unzipped_dir, outdir = [], tempfile.mkdtemp()
        self.extract_zip(inzip, outdir)
        if len([_ for _ in os.listdir(outdir) if 'dcg_k.log' in _]) > 0: unzipped_dir = [outdir]
        else:
            n_outdirs = [outdir] if len([_ for _ in os.listdir(outdir) if _.endswith('zip')]) > 0 else [os.path.join(outdir, _) for _ in
                                                                                                        os.listdir(outdir)]
            for n_outdir in n_outdirs:
                for zip_file in os.listdir(n_outdir):
                    if zip_file.endswith('zip'):
                        unzipped_dir.extend(self.extract_dir(os.path.join(n_outdir, zip_file)))
            shutil.rmtree(outdir)
        for _ in unzipped_dir: self.dir_source[_] = [os.path.basename(inzip)] + self.dir_source.get(_, [])
        return unzipped_dir

    @staticmethod
    def extract_zip(inzip, outdir):
        with ZipFile(inzip, 'r') as zip_file: zip_file.extractall(outdir)

    @staticmethod
    def gunzip_shutil(source, block_size=65536):
        dest = '.'.join(source.split('.')[:-1])
        with gzip.open(source, 'rb') as s_file, open(dest, 'wb') as d_file:
            shutil.copyfileobj(s_file, d_file, block_size)
    
    def process_dcgk_files_to_dict(self):
        merged_dict = {}
        if self.log_dirs is None or len(self.log_dirs) == 0: return merged_dict
        for indir in self.log_dirs:
            indir_intmom = indir
            indir_dcg = indir_intmom
            dcg, immom = {}, {}
            for infile in os.listdir(indir_dcg):
                if infile.endswith('dcg_k.log'):
                    dcg_update = parse_file(os.path.join(indir_dcg, infile))
                    dcg.update(dcg_update)
            for infile in os.listdir(indir_intmom):
                if infile.startswith('intmomlog'):
                    immon_update = parse_file(os.path.join(indir_intmom, infile))
                    if len(immom) == 0:
                        immom.update(immon_update)
                    else:
                        for key in immon_update:
                            if immom.get(key): immom[key].update(immon_update[key])
                elif infile.startswith('rnclog.txt'):
                    sc_update = parse_file(os.path.join(indir_intmom, infile))
            for siteid in immom.keys():
                for mo in immom.get(siteid):
                    match_mo = [_ for _ in dcg.get(siteid).keys() if _.endswith(mo)]
                    if len(match_mo) != 1:
                        print(F'common_procedure --- Could not find single mo in dcg_log for : {siteid}{mo}')
                        continue
                    dcg.get(siteid).get(match_mo[0]).update(immom.get(siteid).get(mo))
            for siteid in sc_update.keys():
                for mo in sc_update.get(siteid):
                    dcg[siteid][mo] = copy.deepcopy(sc_update[siteid][mo])
            # for site in dcg.keys():
            #     merged_dict[site] = copy.deepcopy(dcg.get(site))
            # merged_dict[]
            merged_dict.update(copy.deepcopy(dcg))
            zip_chain = ' > '.join(self.dir_source.get(indir, []))
            for infile in os.listdir(indir_dcg):
                if infile.endswith('dcg_k.log'):
                    dcg_name = infile + '.gz' if os.path.exists(os.path.join(indir_dcg, infile + '.gz')) else infile
                    for siteid in dcg.keys(): self.source_files.setdefault(siteid, {})['dcgk'] = F'{zip_chain} > {dcg_name}'
                if infile.startswith('MSRBS_NODE_MODEL') and infile.endswith('.xml.gz'):
                    with open(os.path.join(indir_dcg, infile), 'rb') as f: mom_data = f.read()
                    for siteid in dcg.keys():
                        self.mom_files[siteid] = mom_data
                        self.source_files.setdefault(siteid, {})['mom'] = F'{zip_chain} > {infile}'
            if len(indir): shutil.rmtree(indir)
        return merged_dict
