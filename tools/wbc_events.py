"""Translate WBC event records without changing their command stream."""
import json,re
from inventory import ROOT,WORK
from event_layout import normalize

TEXT='''6c|결승 진출 확정!<BR>드디어 <STR10> 팀과 우승을 다툽니다.<NEXTPAGE>
194|「월드 베이스볼 클래식 2009」<BR>정상에 오를 팀은 과연 어디일까요?<BR>마침내 최후의 결전입니다!<CLOSE>
2e0|준결승 상대는 <STR10> 팀입니다.<BR>최후의 결전에 나설 팀은 과연…?<CLOSE>
42c|<STR10>에서 등판 제한을 받던 투수는 다음 라운드부터 다시 기용할 수 있습니다.<CLOSE>
578|축하합니다!<BR><STR10>의 <STR5>위 통과가 확정되었습니다!<CLOSENEXT>
6c4|이번 대회의 특별 규칙인<BR>「투구 수 제한」에 관해<BR>설명하겠습니다.<CLOSENEXT>
810|이번 대회는 라운드마다 투수가 던질 수 있는 최대 투구 수가 정해져 있습니다.<BR>제한은 다음과 같습니다.<NEXTPAGE>
938|1라운드　　　　　<RGB 0xf56464>70구<BR><RGB 0xeeeeee>2라운드　　　　　<RGB 0xf56464>85구<BR><RGB 0xeeeeee>준결승 이후　　　<RGB 0xf56464>100구<NEXTPAGE>
a60|이 투구 수를 넘으면 현재 상대 중인 타자까지만 던지고 교체해야 합니다.<CLOSENEXT>
bac|단, 이 게임의 자체 규칙에 따라 벤치에 교체할 투수가 없을 때는 투구 수 제한이 적용되지 않습니다.<NEXTPAGE>
cd4|또한 등판 상황에 따라 다음과 같은 경기 간격을 두어야 합니다.<NEXTPAGE>
dfc|50구 이상 투구　→　<RGB 0xf56464>4경기 휴식<BR><RGB 0xeeeeee>30구 이상 투구　→　<RGB 0xf56464>1경기 휴식<BR><RGB 0xeeeeee>연속 경기 등판　→　<RGB 0xf56464>1경기 휴식<NEXTPAGE>
f24|단, 던질 수 있는 투수가 한 명도 없으면 제한이 일부 완화됩니다.<CLOSE>
1070|이번 대회의 특별 규칙인<BR>「승부치기」에 관해<BR>설명하겠습니다.<CLOSENEXT>
11bc|「승부치기」는 연장 12회까지 승부가 나지 않았을 때 13회부터 적용됩니다.<CLOSENEXT>
1308|「승부치기」에 들어가면 앞 이닝의 마지막 타자와 그 앞 타자를 각각 2루와 1루 주자로 놓고 공격을 시작합니다.<NEXTPAGE>
1430|공격 팀이 득점하기 쉬워져 팽팽한 승부의 균형이 깨지기 쉬워지는 것이 「승부치기」 제도입니다.<CLOSENEXT>
157c|또한 이 게임의 자체 규칙에 따라 15회까지 승부가 나지 않으면 무효 경기로 처리하고 재경기를 합니다.<CLOSE>
16c8|여기서는<BR>「월드 베이스볼 클래식 2009」<BR>대회 개요를 설명하겠습니다.<BR><NEXTPAGE>
17f0|세계 16개 나라와 지역을 대표하는<BR>야구 선수들이 참가하여<BR>우승을 목표로 겨룹니다.<BR><CLOSENEXT>
193c|1라운드는 참가한 16개 팀을 지역별로<BR>4개 조로 나누어 예선을 치릅니다.<BR>각 조 상위 2개 팀이 진출합니다.<CLOSENEXT>
1a88|2라운드는 진출한 팀을 다시 4개 팀씩<BR>나누어 조별 예선을 치릅니다.<BR>여기서도 상위 2개 팀이 진출합니다.<CLOSENEXT>
1bd4|지금까지의 예선 라운드는 모두<BR>「더블 엘리미네이션 방식」으로<BR>진행합니다.<NEXTPAGE>
1cfc|두 번 패하면 대회에서 탈락합니다.<BR>한 번 패해도 예선 통과의 기회는<BR>남아 있습니다.<CLOSENEXT>
1e48|마지막으로 남은 4개 팀이 결승 라운드를<BR>치릅니다.<BR>여기서는 한 번만 패해도 탈락합니다.<NEXTPAGE>
1f70|결승 라운드 두 경기를 모두 이기면<BR>「월드 베이스볼 클래식 2009」의<BR>챔피언이 됩니다.<CLOSE>'''

def main():
    data=(WORK/'assets/GEDATA05.CHK').read_bytes();out={}
    for row in TEXT.splitlines():
        address,ko=row.split('|',1);p=int(address,16)
        ja=data[p:data.index(0,p)].decode('cp932')
        ko=normalize('<RGB 0xeeeeee>'+ko)
        assert re.findall(r'<(?!BR>)[^>]+>',ja)==re.findall(r'<(?!BR>)[^>]+>',ko),(ja,ko)
        out[ja]=ko
    (ROOT/'translation/wbc_events.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')

if __name__=='__main__':main()
