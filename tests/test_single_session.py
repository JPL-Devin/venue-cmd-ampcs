import pytest
import time
import venue_client as vc

@pytest.fixture(scope='module')
def mtak_proc():
    assert vc.session_id_a > 0
    res = vc.start_mtak(server=vc.server_1, sessionIds=[vc.session_id_a])
    print(res.status_code, res.json())
    yield res

    res = vc.shutdown_mtak(server=vc.server_1)
    print(res.status_code)

def test_scmf(mtak_proc):
    if vc.hostname.startswith('psyche'):
        print('send SCMF file')
        res = vc.send_scmf_file(
            server=vc.server_1,
            sessionId=vc.session_id_a, 
            filePath='/teamtools/atlo/production/uplink-files/scmfs/ctt22/10_cmd_no_ops_a.scmf'
        )
        print(res.text)
        assert res.status_code == 200
    
