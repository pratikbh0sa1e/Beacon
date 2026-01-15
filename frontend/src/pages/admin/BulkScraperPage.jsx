import React, { useState } from 'react';
import { Play, AlertCircle, CheckCircle, Loader, Database } from 'lucide-react';
import api from '../../services/api';

const BulkScraperPage = () => {
  const [isScraperRunning, setIsScraperRunning] = useState(false);
  const [scrapingStatus, setScrapingStatus] = useState(null);
  const [logs, setLogs] = useState([]);
  const [stats, setStats] = useState({
    totalFound: 0,
    totalAdded: 0,
    totalSkipped: 0,
    currentSource: ''
  });

  const addLog = (message, type = 'info') => {
    setLogs(prev => [...prev, { message, type, timestamp: new Date().toLocaleTimeString() }]);
  };

  const startBulkScraping = async () => {
    setIsScraperRunning(true);
    setLogs([]);
    setScrapingStatus('running');
    addLog('🚀 Starting bulk scraping with fallback URLs...', 'success');

    try {
      // Trigger bulk scraping
      const response = await api.post('/api/web-scraping/bulk-scrape', {
        max_documents: 1000,
        enable_pagination: true,
        max_pages: 50,
        auto_expand_on_duplicates: true,
        target_new_documents: 500
      });

      addLog(`✅ Scraping job started: Job #${response.data.job_id}`, 'success');
      
      // Poll for status
      pollScrapingStatus(response.data.job_id);
    } catch (error) {
      addLog(`❌ Error: ${error.response?.data?.detail || error.message}`, 'error');
      setIsScraperRunning(false);
      setScrapingStatus('error');
    }
  };

  const pollScrapingStatus = async (jobId) => {
    const interval = setInterval(async () => {
      try {
        const response = await api.get(`/api/web-scraping/bulk-scrape/jobs/${jobId}`);
        const job = response.data;

        setStats({
          totalFound: job.documents_found || 0,
          totalAdded: job.documents_added || 0,
          totalSkipped: job.documents_found - job.documents_added || 0,
          currentSource: job.current_source || ''
        });

        if (job.status === 'completed') {
          clearInterval(interval);
          setIsScraperRunning(false);
          setScrapingStatus('completed');
          addLog(`✅ Scraping completed! Added ${job.documents_added} documents`, 'success');
        } else if (job.status === 'failed') {
          clearInterval(interval);
          setIsScraperRunning(false);
          setScrapingStatus('failed');
          addLog(`❌ Scraping failed: ${job.error_message}`, 'error');
        } else {
          addLog(`📊 Progress: ${job.documents_found} found, ${job.documents_added} added`, 'info');
        }
      } catch (error) {
        clearInterval(interval);
        setIsScraperRunning(false);
        setScrapingStatus('error');
        addLog(`❌ Error checking status: ${error.message}`, 'error');
      }
    }, 3000); // Poll every 3 seconds
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
                <Database className="w-8 h-8 text-blue-600" />
                Bulk Document Scraper
              </h1>
              <p className="text-gray-600 mt-2">
                Scrape 1000+ documents from MoE, UGC, and AICTE with automatic fallback URLs
              </p>
            </div>
            <button
              onClick={startBulkScraping}
              disabled={isScraperRunning}
              className={`flex items-center gap-2 px-6 py-3 rounded-lg font-semibold transition-all ${
                isScraperRunning
                  ? 'bg-gray-400 cursor-not-allowed'
                  : 'bg-blue-600 hover:bg-blue-700 text-white shadow-lg hover:shadow-xl'
              }`}
            >
              {isScraperRunning ? (
                <>
                  <Loader className="w-5 h-5 animate-spin" />
                  Scraping...
                </>
              ) : (
                <>
                  <Play className="w-5 h-5" />
                  Start Bulk Scraping
                </>
              )}
            </button>
          </div>
        </div>

        {/* Stats Cards */}
        {isScraperRunning && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-white rounded-lg shadow p-4">
              <div className="text-sm text-gray-600">Documents Found</div>
              <div className="text-2xl font-bold text-blue-600">{stats.totalFound}</div>
            </div>
            <div className="bg-white rounded-lg shadow p-4">
              <div className="text-sm text-gray-600">Documents Added</div>
              <div className="text-2xl font-bold text-green-600">{stats.totalAdded}</div>
            </div>
            <div className="bg-white rounded-lg shadow p-4">
              <div className="text-sm text-gray-600">Duplicates Skipped</div>
              <div className="text-2xl font-bold text-yellow-600">{stats.totalSkipped}</div>
            </div>
            <div className="bg-white rounded-lg shadow p-4">
              <div className="text-sm text-gray-600">Current Source</div>
              <div className="text-lg font-bold text-purple-600">{stats.currentSource || 'Starting...'}</div>
            </div>
          </div>
        )}

        {/* Features */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Features Enabled</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="flex items-start gap-3">
              <CheckCircle className="w-5 h-5 text-green-600 mt-1" />
              <div>
                <div className="font-semibold">Fallback URLs</div>
                <div className="text-sm text-gray-600">Automatically tries alternative URLs if primary fails</div>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <CheckCircle className="w-5 h-5 text-green-600 mt-1" />
              <div>
                <div className="font-semibold">Auto Pagination</div>
                <div className="text-sm text-gray-600">Searches up to 50 pages per source</div>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <CheckCircle className="w-5 h-5 text-green-600 mt-1" />
              <div>
                <div className="font-semibold">Duplicate Detection</div>
                <div className="text-sm text-gray-600">Skips already downloaded documents</div>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <CheckCircle className="w-5 h-5 text-green-600 mt-1" />
              <div>
                <div className="font-semibold">Auto Expansion</div>
                <div className="text-sm text-gray-600">Searches more pages when duplicates found</div>
              </div>
            </div>
          </div>
        </div>

        {/* Logs */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Scraping Logs</h2>
          <div className="bg-gray-900 rounded-lg p-4 h-96 overflow-y-auto font-mono text-sm">
            {logs.length === 0 ? (
              <div className="text-gray-500 text-center py-8">
                Click "Start Bulk Scraping" to begin...
              </div>
            ) : (
              logs.map((log, index) => (
                <div
                  key={index}
                  className={`mb-2 ${
                    log.type === 'error'
                      ? 'text-red-400'
                      : log.type === 'success'
                      ? 'text-green-400'
                      : 'text-gray-300'
                  }`}
                >
                  <span className="text-gray-500">[{log.timestamp}]</span> {log.message}
                </div>
              ))
            )}
          </div>
        </div>

        {/* Status Banner */}
        {scrapingStatus === 'completed' && (
          <div className="mt-6 bg-green-50 border border-green-200 rounded-lg p-4 flex items-center gap-3">
            <CheckCircle className="w-6 h-6 text-green-6raperPage;
lkSc Buult
export defa
;
};>
  )    </divv>
     </di  )}
 iv>
      /d   <    v>
       </di        div>
r details</above fologs ">Check the d-700text-re"text-sm lassName=      <div c      /div>
  Failed<raping 00">Scred-9t-exbold t-semiontme="fclassNa <div             div>
     <
        ed-600" />xt-r-6 h-6 tesName="wclastCircle ler       <A  
   r gap-3">tes-cen-4 flex item-lg pounded-200 r border-redrder-50 boedbg-r6 t-me="massNa  <div cl
        (ailed' && tatus === 'f  {scrapingS            )}

v>
      </di   iv>
   </d      >
           </div
         the databaseuments to docalAdded} stats.totdded {ssfully ace     Suc           een-700">
sm text-grme="text-v classNa        <didiv>
      ted!</Compleg >Scrapin-900" text-greenmibold-se="fontmeNav class      <di     div>
            <00" />
   