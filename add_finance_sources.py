"""
Add finance-related sources for scraping
Ministry of Finance, RBI, SEBI, etc.
"""
import sys
sys.path.insert(0, '.')

from backend.database import SessionLocal, WebScrapingSource
from datetime import datetime
import json

def add_finance_sources():
    """Add finance-related scraping sources"""
    print("="*80)
    print("ADDING FINANCE SOURCES")
    print("="*80)
    
    db = SessionLocal()
    
    try:
        finance_sources = [
            {
                "name": "Ministry of Finance",
                "url": "https://www.finmin.nic.in",
                "source_type": "government",
                "description": "Ministry of Finance - Policies, Circulars, Notifications",
                "credibility_score": 10,
                "fallback_urls": [
                    "https://finmin.nic.in",
                    "https://www.finmin.nic.in/documents",
                    "https://www.finmin.nic.in/reports",
                    "https://www.finmin.nic.in/notifications",
                    "https://dea.gov.in",  # Department of Economic Affairs
                    "https://dor.gov.in",  # Department of Revenue
                ]
            },
            {
                "name": "Reserve Bank of India",
                "url": "https://www.rbi.org.in",
                "source_type": "government",
                "description": "RBI - Circulars, Notifications, Guidelines",
                "credibility_score": 10,
                "fallback_urls": [
                    "https://rbi.org.in",
                    "https://www.rbi.org.in/Scripts/BS_ViewMasCirculardetails.aspx",
                    "https://www.rbi.org.in/Scripts/NotificationUser.aspx",
                    "https://www.rbi.org.in/Scripts/BS_PressReleaseDisplay.aspx",
                    "https://rbidocs.rbi.org.in",
                ]
            },
            {
                "name": "SEBI",
                "url": "https://www.sebi.gov.in",
                "source_type": "government",
                "description": "Securities and Exchange Board of India - Circulars, Guidelines",
                "credibility_score": 10,
                "fallback_urls": [
                    "https://sebi.gov.in",
                    "https://www.sebi.gov.in/legal/circulars.html",
                    "https://www.sebi.gov.in/legal/master-circulars.html",
                    "https://www.sebi.gov.in/sebiweb/home/HomeAction.do?doListing=yes&sid=1&ssid=1&smid=0",
                ]
            },
            {
                "name": "Income Tax Department",
                "url": "https://www.incometax.gov.in",
                "source_type": "government",
                "description": "Income Tax Department - Circulars, Notifications, Forms",
                "credibility_score": 10,
                "fallback_urls": [
                    "https://incometax.gov.in",
                    "https://www.incometax.gov.in/iec/foportal/",
                    "https://www.incometaxindia.gov.in",
                ]
            },
            {
                "name": "GST Council",
                "url": "https://www.gst.gov.in",
                "source_type": "government",
                "description": "GST Council - Notifications, Circulars, Guidelines",
                "credibility_score": 10,
                "fallback_urls": [
                    "https://gst.gov.in",
                    "https://www.cbic.gov.in",  # Central Board of Indirect Taxes
                    "https://www.cbic.gov.in/resources//htdocs-cbec/gst/index.html",
                ]
            },
            {
                "name": "NITI Aayog",
                "url": "https://www.niti.gov.in",
                "source_type": "government",
                "description": "NITI Aayog - Policy Papers, Reports, Publications",
                "credibility_score": 10,
                "fal
_sources()nance   add_fi:
 ain__""__m_name__ == 

if _ose()
b.cl
        dinally:  f       
  
 80)t("="* prin     
  PING")CRA READY FOR SURCESSOFINANCE    print("80)
     " + "="*nt("\n        pri  
     crape}")
 nts_per_sdocumerce.max_{souax docs: t(f"  M   prin
         erified}").ved: {source"  Verifi    print(f        
led}")g_enabapine.scr{sourc Enabled: f"       print(     }")
 {source.urlL: f"  UR  print(          )
:".name}\n{sourceprint(f"           es:
 urcl_source in alr so    fo      
    .all()
  )
        )e_sources]financin me'] for s [s['naame.in_(ce.nScrapingSoureb  W        ter(
  gSource).filpinScray(Webs = db.querl_source       al")
 ces:Finance Sour"\nAll t(    prins
     sourceShow all      #       
   "*80)
 "=(  print")
      sources existing d}ed {update✅ Updatprint(f"      ")
   sourcesnew{added} "✅ Added rint(f      p*80)
  nt("="     pri       
   .commit()
    db     
        )
     print(
       ore")) - 3} mk_urls']ac['fallbsource_data.. and {len( ."   print(f      
          ]) > 3:s'url'fallback_urce_data[n(sof le        i
    "){i}. {url}nt(f"    pri               
 ):s'][:3], 1allback_urlurce_data['f(sorateme enu infor i, url           ls'])}")
 llback_urrce_data['fa(sou URLs: {lenFallback"   print(f         
  }")'url']a[rce_datrimary: {sount(f"  P        pri URLs
        # Show  
              ]}")
    e''namata[{source_dd: "✓ Adde     print(f        
   dded += 1  a         urce)
     so    db.add(        
                  )
             e=100
     ts_per_scrap max_documen                   
data),(fallback_mpsson.duon_notes=jtiverifica                   True,
 ified=    ver               d=True,
 nablescraping_e              "],
      scoreedibility_crrce_data["ouity_score=scredibil              "],
      criptiona["des=source_dationriptsc        de         ,
   e"]ce_typta["sourource_daurce_type=s         so    ],
       ata["url"urce_d     url=so           "],
    ["namece_datasour  name=               (
   pingSourcebScrace = Weour         s  
                        }
         )
    ormat(().isof.utcnowmeateti_updated': dlast        '       
     : True,abled'raping_enep_sc     'de               ue,
ed': Trblion_enal_rotat   'ur           s'],
      url['fallback_datals': source_allback_ur 'f               
    k_data = {     fallbac           new source
# Create                 else:
 
           ']}")namedata['ed: {source_datrint(f"✓ Up         p= 1
       d + update             
              w()
    time.utcnoat = dateg.updated_istinex                )
llback_datadumps(faon.s = jsication_noteerifisting.v       ex
               }        
  t()formautcnow().isotetime.dated': dat_up    'las      
          bled': True,aping_ena'deep_scr                    
d': True,on_enable'url_rotati                   s'],
 back_url'fallsource_data[s': k_urlfallbac    '                = {
a atk_dbacfall             RLs
   ack Uate fallb# Upd              
                ore"]
  _sclity"credibiurce_data[soty_score = credibiling.  existi           ion"]
   "descriptta[ = source_daptioning.descriexist              "]
  "urlurce_data[ so =existing.url            
    ng sourcetipdate exis  # U            
  ng:existiif                 
      
  .first()     )   "]
    amee_data["name == sourc.ngSourceebScrapin   W        (
     ce).filterngSourapiy(WebScr = db.quer existing          sts
  already exisourcek if  Chec   #
         :ources_sancefinata in ource_dr s     fo   
    = 0
         updated 0
    dded =
        a        ]
    },
                      ]
       ars",
   v.in/circuli.gow.irdatps://ww      "ht          ons",
    regulatiin/w.irdai.gov./wwhttps:/  "                .in",
  //irdai.gov"https:                : [
    ack_urls"lb      "fal      ,
    core": 10_sdibility "cre               lines",
lars, Guidey - Circuent Authoritvelopmory and DeRegulatnsurance ": "Iriptiondesc        "
        ment",ern"gove_type":    "sourc         ,
    .in"govrdai.ww.ihttps://w"":   "url             
 ",: "IRDAI"me    "na                {
           },
             ]
           l",
 s.htmortata-and-rep/en/d/globalt/mcaov.in/contenw.mca.gps://ww  "htt                 ",
 rules.htmls-/actglobal/ent/mca/ntenn/cov.i//www.mca.gottps: "h          
         n",ov.ittps://mca.g        "h       
     urls": [k_lbac       "fal,
         _score": 10ityibil  "cred            ,
  cations"ifirs, NotlaCircumpany Law, MCA - Co"on": cripti"des             ment",
   ern": "gove_type     "sourc         ",
  .mca.gov.inwwttps://w": "h   "url            irs",
 rporate Affatry of Coe": "Minisam"n                 {
               },
        ]
               s",
 /report.niti.gov.in//wwwttps:    "h           ts",
     documenov.in/.niti.gwwhttps://w     "              ",
 .gov.in//niti"https:                   rls": [
 lback_u