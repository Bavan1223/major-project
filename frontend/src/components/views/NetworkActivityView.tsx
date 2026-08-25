import React, { useMemo, useState } from 'react';
import { useSoc } from '../../context/SocContext';
import { NetworkConnection } from '../../types';
import {
  Network,
  Search,
  ArrowUpDown,
  Globe,
  Repeat,
  Terminal,
  AlertTriangle,
  ShieldAlert,
} from 'lucide-react';

export const NetworkActivityView: React.FC = () => {
  const {
    connections,
    setSelectedProcess,
    processes,
    setActiveTab,
  } = useSoc();

  const [filterText, setFilterText] =
    useState('');

  const [selectedStatusFilter, setSelectedStatusFilter] =
    useState<string>('ALL');

  const [selectedConnection, setSelectedConnection] =
    useState<NetworkConnection | null>(null);

  /*
   * ==========================================================
   * REAL NETWORK TELEMETRY
   * ==========================================================
   *
   * The connections array is populated from:
   *
   *     GET /api/network
   *
   * Do not use hardcoded/demo network statistics here.
   */

  const establishedConnections =
    useMemo(
      () =>
        connections.filter(
          (conn) =>
            conn.status === 'ESTABLISHED' ||
            conn.status === 'ESTAB'
        ),
      [connections]
    );

  const uniqueRemoteIPs =
    useMemo(() => {
      const ips = new Set<string>();

      connections.forEach((conn) => {
        const address =
          conn.remoteAddress || '';

        const ip =
          address.includes(':')
            ? address.substring(
                0,
                address.lastIndexOf(':')
              )
            : address;

        if (
          ip &&
          ip !== 'Unknown' &&
          ip !== '*'
        ) {
          ips.add(ip);
        }
      });

      return ips.size;
    }, [connections]);

  const repeatedConnections =
    useMemo(
      () =>
        connections.filter(
          (conn) =>
            conn.indicator ===
            'repeated_connection_to_endpoint' ||
            conn.indicator ===
            'repeated_connection'
        ),
      [connections]
    );

  const filteredConnections =
    useMemo(() => {

      return connections.filter(
        (conn) => {

          /*
           * Convert the real backend indicator
           * into the filter categories used by
           * the UI.
           */

          const isRepeated =
            conn.indicator ===
              'repeated_connection_to_endpoint' ||
            conn.indicator ===
              'repeated_connection';

          const isSuspicious =
            isRepeated;

          const isAnomaly =
            conn.indicator !==
              'new_established_connection' &&
            !isRepeated;

          if (
            selectedStatusFilter ===
            'SUSPICIOUS' &&
            !isSuspicious
          ) {
            return false;
          }

          if (
            selectedStatusFilter ===
            'ANOMALY' &&
            !isAnomaly
          ) {
            return false;
          }

          if (
            selectedStatusFilter ===
            'NORMAL' &&
            (isSuspicious || isAnomaly)
          ) {
            return false;
          }

          if (
            filterText.trim() !== ''
          ) {

            const q =
              filterText
                .toLowerCase()
                .trim();

            return (
              (conn.process || '')
                .toLowerCase()
                .includes(q) ||

              (conn.localAddress || '')
                .toLowerCase()
                .includes(q) ||

              (conn.remoteAddress || '')
                .toLowerCase()
                .includes(q) ||

              String(
                conn.pid ?? ''
              ).includes(q) ||

              (conn.status || '')
                .toLowerCase()
                .includes(q) ||

              (conn.indicator || '')
                .toLowerCase()
                .includes(q)
            );
          }

          return true;
        }
      );

    }, [
      connections,
      filterText,
      selectedStatusFilter,
    ]);

  /*
   * ==========================================================
   * UI
   * ==========================================================
   */

  return (
    <div className="flex flex-col w-full p-4 gap-3 bg-[#10131a] min-h-[calc(100vh-64px)] select-none">

      {/* ======================================================
          REAL NETWORK STATISTICS
          ====================================================== */}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">

        {/* ESTABLISHED */}

        <div className="bg-[#1d2027] rounded p-4 border border-[#424754] relative overflow-hidden">

          <div className="absolute right-0 top-0 w-32 h-32 bg-[#adc6ff]/5 rounded-full blur-2xl -mr-16 -mt-16" />

          <div className="flex justify-between items-start mb-2">

            <div className="flex items-center gap-1.5 text-[#c2c6d6]">

              <ArrowUpDown className="w-4 h-4 text-[#adc6ff]" />

              <span className="font-mono text-[10px] font-bold tracking-wider uppercase">
                ESTABLISHED CONNECTIONS
              </span>

            </div>

            <span className="font-mono text-[8px] text-[#4edea3] border border-[#4edea3]/30 px-2 py-1 rounded">
              LIVE
            </span>

          </div>

          <div className="flex items-end gap-2">

            <span className="text-[26px] font-bold text-[#e1e2ec] font-mono leading-none">
              {establishedConnections.length}
            </span>

            <span className="font-mono text-[11px] text-[#c2c6d6] mb-0.5">
              observed
            </span>

          </div>

          <div className="mt-4 h-1.5 w-full bg-[#272a31] rounded-full overflow-hidden">

            <div
              className="h-full bg-[#adc6ff] rounded-full transition-all"
              style={{
                width:
                  establishedConnections.length > 0
                    ? '100%'
                    : '0%',
              }}
            />

          </div>

        </div>


        {/* UNIQUE REMOTE IPs */}

        <div className="bg-[#1d2027] rounded p-4 border border-[#424754] relative overflow-hidden">

          <div className="absolute right-0 top-0 w-32 h-32 bg-[#4edea3]/5 rounded-full blur-2xl -mr-16 -mt-16" />

          <div className="flex justify-between items-start mb-2">

            <div className="flex items-center gap-1.5 text-[#c2c6d6]">

              <Globe className="w-4 h-4 text-[#4edea3]" />

              <span className="font-mono text-[10px] font-bold tracking-wider uppercase">
                UNIQUE REMOTE IPs
              </span>

            </div>

            <span className="font-mono text-[8px] text-[#4edea3] border border-[#4edea3]/30 px-2 py-1 rounded">
              LIVE
            </span>

          </div>

          <div className="flex items-end gap-2">

            <span className="text-[26px] font-bold text-[#e1e2ec] font-mono leading-none">
              {uniqueRemoteIPs}
            </span>

            <span className="font-mono text-[11px] text-[#c2c6d6] mb-0.5">
              observed
            </span>

          </div>

          <div className="mt-4 flex gap-1 h-7 items-end">

            {connections.length === 0 ? (

              <div className="w-full h-[20%] bg-[#4edea3]/20 rounded" />

            ) : (

              Array.from(
                { length: 8 },
                (_, index) => {

                  const height =
                    Math.min(
                      100,
                      Math.max(
                        15,
                        Math.round(
                          (
                            connections.length /
                            Math.max(
                              1,
                              connections.length
                            )
                          ) *
                            (25 + index * 9)
                        )
                      )
                    );

                  return (
                    <div
                      key={index}
                      className="w-full bg-[#4edea3]/60 rounded"
                      style={{
                        height: `${height}%`,
                      }}
                    />
                  );

                }
              )

            )}

          </div>

        </div>


        {/* REPEATED */}

        <div className="bg-[#1d2027] rounded p-4 border border-[#424754] relative overflow-hidden">

          <div className="absolute right-0 top-0 w-32 h-32 bg-[#ffb4ab]/5 rounded-full blur-2xl -mr-16 -mt-16" />

          <div className="flex justify-between items-start mb-2">

            <div className="flex items-center gap-1.5 text-[#c2c6d6]">

              <Repeat className="w-4 h-4 text-[#ffb4ab]" />

              <span className="font-mono text-[10px] font-bold tracking-wider uppercase">
                REPEATED CONNECTIONS
              </span>

            </div>

            <span className="font-mono text-[8px] text-[#ffb4ab] border border-[#ffb4ab]/30 px-2 py-1 rounded">
              INDICATOR
            </span>

          </div>

          <div className="flex items-end gap-2">

            <span className="text-[26px] font-bold text-[#e1e2ec] font-mono leading-none">
              {repeatedConnections.length}
            </span>

            <span className="font-mono text-[11px] text-[#c2c6d6] mb-0.5">
              observed
            </span>

          </div>

          <div className="mt-4 relative h-7 w-full">

            <svg
              className="absolute inset-0 w-full h-full"
              preserveAspectRatio="none"
              viewBox="0 0 100 20"
            >

              <path
                className="text-[#ffb4ab]/20"
                d="M0,15 Q10,5 20,10 T40,15 T60,5 T80,18 T100,8 L100,20 L0,20 Z"
                fill="currentColor"
              />

              <path
                className="text-[#ffb4ab]"
                d="M0,15 Q10,5 20,10 T40,15 T60,5 T80,18 T100,8"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.5"
              />

            </svg>

          </div>

        </div>

      </div>


      {/* ======================================================
          CONNECTION TABLE
          ====================================================== */}

      <div className="bg-[#1d2027] rounded border border-[#424754] flex flex-col flex-1 overflow-hidden">

        {/* HEADER */}

        <div className="p-3 border-b border-[#424754] flex flex-wrap justify-between items-center bg-[#272a31]/50 gap-2">

          <div className="flex items-center gap-2">

            <Network className="w-5 h-5 text-[#adc6ff]" />

            <span className="font-mono text-[11px] font-bold text-[#e1e2ec] tracking-wider uppercase">
              LIVE NETWORK CONNECTIONS
            </span>

            <span className="font-mono text-[9px] text-[#4edea3]">
              {connections.length} EVENTS
            </span>

          </div>


          <div className="flex items-center gap-2">

            <div className="relative">

              <Search className="w-4 h-4 absolute left-2.5 top-1/2 -translate-y-1/2 text-[#8c909f]" />

              <input
                type="text"
                value={filterText}
                onChange={(e) =>
                  setFilterText(
                    e.target.value
                  )
                }
                placeholder="Filter by IP, Port, Process..."
                className="bg-[#10131a] border border-[#424754] rounded pl-8 pr-3 py-1 font-mono text-[11px] text-[#e1e2ec] focus:outline-none focus:border-[#adc6ff] w-64 placeholder-[#8c909f]"
              />

            </div>


            <div className="flex gap-1">

              {[
                'ALL',
                'SUSPICIOUS',
                'ANOMALY',
                'NORMAL',
              ].map((st) => (

                <button
                  key={st}
                  onClick={() =>
                    setSelectedStatusFilter(
                      st
                    )
                  }
                  className={`px-2 py-1 rounded font-mono text-[9px] font-bold border ${
                    selectedStatusFilter === st
                      ? 'bg-[#adc6ff] text-[#002e6a] border-[#adc6ff]'
                      : 'bg-[#10131a] text-[#c2c6d6] border-[#424754] hover:bg-[#272a31]'
                  }`}
                >
                  {st}
                </button>

              ))}

            </div>

          </div>

        </div>


        {/* TABLE */}

        <div className="overflow-auto max-h-[540px]">

          <table className="w-full text-left border-collapse font-mono text-[11px]">

            <thead className="sticky top-0 bg-[#32353c] border-b border-[#424754] z-10 text-[#c2c6d6] text-[10px] uppercase font-bold tracking-wider">

              <tr>

                <th className="p-2.5 pl-4 whitespace-nowrap w-24">
                  TIME (UTC)
                </th>

                <th className="p-2.5 whitespace-nowrap">
                  PROCESS
                </th>

                <th className="p-2.5 whitespace-nowrap w-20">
                  PID
                </th>

                <th className="p-2.5 whitespace-nowrap">
                  LOCAL ADDRESS
                </th>

                <th className="p-2.5 whitespace-nowrap">
                  REMOTE ADDRESS
                </th>

                <th className="p-2.5 whitespace-nowrap w-24">
                  STATUS
                </th>

                <th className="p-2.5 pr-4 whitespace-nowrap w-40 text-right">
                  INDICATOR
                </th>

              </tr>

            </thead>


            <tbody className="divide-y divide-[#424754]/30 text-[#e1e2ec]">

              {filteredConnections.map(
                (conn) => {

                  const isRepeated =
                    conn.indicator ===
                      'repeated_connection_to_endpoint' ||
                    conn.indicator ===
                      'repeated_connection';

                  const isNewConnection =
                    conn.indicator ===
                    'new_established_connection';

                  return (

                    <tr
                      key={conn.id}
                      onClick={() => {

                        setSelectedConnection(
                          conn
                        );

                        const matchedProcess =
                          processes.find(
                            (process) =>
                              process.pid ===
                              conn.pid
                          );

                        if (
                          matchedProcess
                        ) {
                          setSelectedProcess(
                            matchedProcess
                          );
                        }

                      }}
                      className={`hover:bg-[#272a31] transition-colors group cursor-pointer ${
                        isRepeated
                          ? 'bg-[#93000a]/15 border-l-2 border-l-[#ffb4ab]'
                          : ''
                      }`}
                    >

                      <td className="p-2.5 pl-4 text-[#c2c6d6]">
                        {conn.time}
                      </td>


                      <td className="p-2.5">

                        <div className="flex items-center gap-2">

                          {isRepeated ? (

                            <AlertTriangle className="w-3.5 h-3.5 text-[#ffb4ab]" />

                          ) : (

                            <Terminal className="w-3.5 h-3.5 text-[#8c909f]" />

                          )}

                          <span
                            className={
                              isRepeated
                                ? 'text-[#ffb4ab] font-bold'
                                : 'text-[#adc6ff]'
                            }
                          >
                            {conn.process ||
                              'Unknown'}
                          </span>

                        </div>

                      </td>


                      <td className="p-2.5 text-[#c2c6d6]">
                        {conn.pid ??
                          '—'}
                      </td>


                      <td className="p-2.5 text-[#e1e2ec]">
                        {conn.localAddress ||
                          'Unknown'}
                      </td>


                      <td className="p-2.5 font-bold text-[#e1e2ec]">
                        {conn.remoteAddress ||
                          'Unknown'}
                      </td>


                      <td className="p-2.5">

                        {conn.status ===
                          'ESTABLISHED' ||
                        conn.status ===
                          'ESTAB' ? (

                          <span className="text-[#4edea3] flex items-center gap-1.5">

                            <span className="w-1.5 h-1.5 rounded-full bg-[#4edea3]" />

                            ESTABLISHED

                          </span>

                        ) : (

                          <span className="text-[#c2c6d6] flex items-center gap-1.5">

                            <span className="w-1.5 h-1.5 rounded-full bg-[#8c909f]" />

                            {conn.status ||
                              'UNKNOWN'}

                          </span>

                        )}

                      </td>


                      <td className="p-2.5 pr-4 text-right">

                        {isRepeated ? (

                          <span className="inline-block px-2 py-0.5 border border-[#ffb4ab] bg-[#93000a]/40 rounded text-[#ffb4ab] font-bold text-[9px]">
                            REPEATED ENDPOINT
                          </span>

                        ) : isNewConnection ? (

                          <span className="inline-block px-2 py-0.5 border border-[#424754] rounded text-[#c2c6d6] bg-[#10131a] text-[9px]">
                            NEW CONNECTION
                          </span>

                        ) : (

                          <span className="inline-block px-2 py-0.5 border border-[#424754] rounded text-[#c2c6d6] bg-[#10131a] text-[9px]">
                            {conn.indicator ||
                              'OBSERVED'}
                          </span>

                        )}

                      </td>

                    </tr>

                  );

                }
              )}

            </tbody>

          </table>

        </div>

      </div>


      {/* ======================================================
          SOCKET INSPECTION
          ====================================================== */}

      {selectedConnection && (

        <div className="fixed inset-0 bg-black/70 backdrop-blur-xs z-50 flex items-center justify-center p-4">

          <div className="bg-[#191b23] border border-[#424754] rounded-lg max-w-md w-full p-5 shadow-2xl space-y-4 font-mono text-[11px]">

            <div className="flex items-center justify-between border-b border-[#424754] pb-3">

              <div className="flex items-center gap-2">

                <Globe className="w-5 h-5 text-[#adc6ff]" />

                <h3 className="text-[15px] font-bold text-[#e1e2ec]">
                  Socket Inspection
                </h3>

              </div>

              <button
                onClick={() =>
                  setSelectedConnection(
                    null
                  )
                }
                className="text-[#8c909f] hover:text-[#e1e2ec]"
              >
                ✕
              </button>

            </div>


            <div className="space-y-3">

              <div className="flex justify-between gap-4">

                <span className="text-[#8c909f]">
                  PROCESS
                </span>

                <span className="text-[#e1e2ec] text-right">
                  {selectedConnection.process ||
                    'Unknown'}
                </span>

              </div>


              <div className="flex justify-between gap-4">

                <span className="text-[#8c909f]">
                  PID
                </span>

                <span className="text-[#e1e2ec]">
                  {selectedConnection.pid ??
                    'Unknown'}
                </span>

              </div>


              <div className="flex justify-between gap-4">

                <span className="text-[#8c909f]">
                  LOCAL
                </span>

                <span className="text-[#adc6ff] text-right">
                  {selectedConnection.localAddress ||
                    'Unknown'}
                </span>

              </div>


              <div className="flex justify-between gap-4">

                <span className="text-[#8c909f]">
                  REMOTE
                </span>

                <span className="text-[#adc6ff] text-right">
                  {selectedConnection.remoteAddress ||
                    'Unknown'}
                </span>

              </div>


              <div className="flex justify-between gap-4">

                <span className="text-[#8c909f]">
                  STATE
                </span>

                <span className="text-[#4edea3]">
                  {selectedConnection.status ||
                    'Unknown'}
                </span>

              </div>


              <div className="flex justify-between gap-4">

                <span className="text-[#8c909f]">
                  TIMESTAMP
                </span>

                <span className="text-[#e1e2ec]">
                  {selectedConnection.time}
                </span>

              </div>


              <div className="flex justify-between gap-4">

                <span className="text-[#8c909f]">
                  INDICATOR
                </span>

                <span className="text-[#ffb786] text-right">
                  {selectedConnection.indicator ||
                    'observed'}
                </span>

              </div>

            </div>


            <div className="border-t border-[#424754] pt-3 text-[#8c909f] text-[10px] leading-relaxed">

              Network indicators are behavioral evidence only.
              A repeated connection does not by itself prove
              command-and-control or ransomware activity.

            </div>


            <div className="flex gap-2">

              <button
                onClick={() => {

                  const matchedProcess =
                    processes.find(
                      (process) =>
                        process.pid ===
                        selectedConnection.pid
                    );

                  if (
                    matchedProcess
                  ) {
                    setSelectedProcess(
                      matchedProcess
                    );

                    setActiveTab(
                      'process-activity'
                    );
                  }

                  setSelectedConnection(
                    null
                  );

                }}
                className="flex-1 bg-[#adc6ff] text-[#002e6a] font-mono text-[10px] font-bold py-2 rounded hover:bg-white transition-colors"
              >
                VIEW PROCESS
              </button>


              <button
                onClick={() =>
                  setSelectedConnection(
                    null
                  )
                }
                className="px-4 bg-[#272a31] text-[#c2c6d6] border border-[#424754] font-mono text-[10px] font-bold py-2 rounded hover:bg-[#32353c]"
              >
                CLOSE
              </button>

            </div>

          </div>

        </div>

      )}

    </div>
  );
};
