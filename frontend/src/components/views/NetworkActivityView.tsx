import React, { useMemo, useState } from 'react';
import { useSoc } from '../../context/SocContext';
import {
  NetworkConnection,
} from '../../types';

import {
  Network,
  Search,
  ArrowUpDown,
  Globe,
  Repeat,
  Terminal,
  AlertTriangle,
} from 'lucide-react';


export const NetworkActivityView: React.FC = () => {

  const {
    connections,
    processes,
    setSelectedProcess,
    setActiveTab,
  } = useSoc();


  const [filterText, setFilterText] =
    useState('');

  const [selectedStatusFilter, setSelectedStatusFilter] =
    useState('ALL');

  const [selectedConnection, setSelectedConnection] =
    useState<NetworkConnection | null>(null);


  /*
   * ==========================================================
   * REAL NETWORK TELEMETRY
   * ==========================================================
   *
   * connections comes from:
   *
   *     GET /api/network
   *
   * No hardcoded network statistics.
   */


  const establishedConnections =
    useMemo(() => {

      return connections.filter(
        (connection) =>
          connection.status === 'ESTABLISHED' ||
          connection.status === 'ESTAB'
      );

    }, [connections]);


  const uniqueRemoteIPs =
    useMemo(() => {

      const ips =
        new Set<string>();

      connections.forEach(
        (connection) => {

          const address =
            connection.remoteAddress || '';

          if (!address) {
            return;
          }

          /*
           * IPv4:port
           */
          const lastColon =
            address.lastIndexOf(':');

          const ip =
            lastColon > -1
              ? address.substring(
                  0,
                  lastColon
                )
              : address;

          if (
            ip &&
            ip !== 'Unknown' &&
            ip !== '*'
          ) {
            ips.add(ip);
          }

        }
      );

      return ips.size;

    }, [connections]);


  const repeatedConnections =
    useMemo(() => {

      return connections.filter(
        (connection) =>
          connection.indicator ===
            'repeated_connection_to_endpoint' ||
          connection.indicator ===
            'repeated_connection'
      );

    }, [connections]);


  /*
   * ==========================================================
   * FILTERING
   * ==========================================================
   */

  const filteredConnections =
    useMemo(() => {

      return connections.filter(
        (connection) => {

          const indicator =
            (
              connection.indicator ||
              ''
            ).toLowerCase();


          const isRepeated =
            indicator ===
              'repeated_connection_to_endpoint' ||
            indicator ===
              'repeated_connection';


          const isNormal =
            indicator ===
            'new_established_connection';


          if (
            selectedStatusFilter ===
            'SUSPICIOUS' &&
            !isRepeated
          ) {
            return false;
          }


          if (
            selectedStatusFilter ===
            'NORMAL' &&
            !isNormal
          ) {
            return false;
          }


          if (
            selectedStatusFilter ===
            'ANOMALY' &&
            isNormal
          ) {
            return false;
          }


          const query =
            filterText
              .trim()
              .toLowerCase();


          if (!query) {
            return true;
          }


          return (

            (
              connection.process ||
              ''
            )
              .toLowerCase()
              .includes(query)

            ||

            (
              connection.localAddress ||
              ''
            )
              .toLowerCase()
              .includes(query)

            ||

            (
              connection.remoteAddress ||
              ''
            )
              .toLowerCase()
              .includes(query)

            ||

            String(
              connection.pid ?? ''
            ).includes(query)

            ||

            (
              connection.status ||
              ''
            )
              .toLowerCase()
              .includes(query)

            ||

            (
              connection.indicator ||
              ''
            )
              .toLowerCase()
              .includes(query)

          );

        }
      );

    }, [
      connections,
      filterText,
      selectedStatusFilter,
    ]);


  /*
   * ==========================================================
   * CONNECTION CLICK
   * ==========================================================
   */

  const inspectConnection =
    (
      connection: NetworkConnection
    ) => {

      setSelectedConnection(
        connection
      );

    };


  /*
   * ==========================================================
   * RENDER
   * ==========================================================
   */

  return (

    <div className="flex flex-col w-full p-4 gap-3 bg-[#10131a] min-h-[calc(100vh-64px)]">


      {/* ======================================================
          REAL NETWORK STATISTICS
          ====================================================== */}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">


        {/* ESTABLISHED CONNECTIONS */}

        <div className="bg-[#1d2027] rounded p-4 border border-[#424754]">

          <div className="flex items-center justify-between mb-3">

            <div className="flex items-center gap-2">

              <ArrowUpDown className="w-4 h-4 text-[#adc6ff]" />

              <span className="font-mono text-[10px] font-bold text-[#c2c6d6] uppercase tracking-wider">
                Established Connections
              </span>

            </div>

            <span className="font-mono text-[8px] text-[#4edea3] border border-[#4edea3]/30 px-2 py-1 rounded">
              LIVE
            </span>

          </div>


          <div className="flex items-end gap-2">

            <span className="text-[28px] font-bold font-mono text-[#e1e2ec]">
              {establishedConnections.length}
            </span>

            <span className="text-[10px] font-mono text-[#8c909f] mb-1">
              observed
            </span>

          </div>

        </div>


        {/* UNIQUE REMOTE IPS */}

        <div className="bg-[#1d2027] rounded p-4 border border-[#424754]">

          <div className="flex items-center justify-between mb-3">

            <div className="flex items-center gap-2">

              <Globe className="w-4 h-4 text-[#4edea3]" />

              <span className="font-mono text-[10px] font-bold text-[#c2c6d6] uppercase tracking-wider">
                Unique Remote IPs
              </span>

            </div>

            <span className="font-mono text-[8px] text-[#4edea3] border border-[#4edea3]/30 px-2 py-1 rounded">
              LIVE
            </span>

          </div>


          <div className="flex items-end gap-2">

            <span className="text-[28px] font-bold font-mono text-[#e1e2ec]">
              {uniqueRemoteIPs}
            </span>

            <span className="text-[10px] font-mono text-[#8c909f] mb-1">
              observed
            </span>

          </div>

        </div>


        {/* REPEATED CONNECTIONS */}

        <div className="bg-[#1d2027] rounded p-4 border border-[#424754]">

          <div className="flex items-center justify-between mb-3">

            <div className="flex items-center gap-2">

              <Repeat className="w-4 h-4 text-[#ffb4ab]" />

              <span className="font-mono text-[10px] font-bold text-[#c2c6d6] uppercase tracking-wider">
                Repeated Connections
              </span>

            </div>

            <span className="font-mono text-[8px] text-[#ffb4ab] border border-[#ffb4ab]/30 px-2 py-1 rounded">
              INDICATOR
            </span>

          </div>


          <div className="flex items-end gap-2">

            <span className="text-[28px] font-bold font-mono text-[#e1e2ec]">
              {repeatedConnections.length}
            </span>

            <span className="text-[10px] font-mono text-[#8c909f] mb-1">
              observed
            </span>

          </div>

        </div>

      </div>


      {/* ======================================================
          LIVE NETWORK TABLE
          ====================================================== */}

      <div className="bg-[#1d2027] rounded border border-[#424754] flex flex-col flex-1 overflow-hidden">


        {/* HEADER */}

        <div className="p-3 border-b border-[#424754] flex flex-wrap justify-between items-center gap-2 bg-[#272a31]/50">


          <div className="flex items-center gap-2">

            <Network className="w-5 h-5 text-[#adc6ff]" />

            <span className="font-mono text-[11px] font-bold text-[#e1e2ec] tracking-wider uppercase">
              Live Network Connections
            </span>

            <span className="font-mono text-[9px] text-[#4edea3]">
              {connections.length} EVENTS
            </span>

          </div>


          <div className="flex items-center gap-2">


            {/* SEARCH */}

            <div className="relative">

              <Search className="w-4 h-4 absolute left-2.5 top-1/2 -translate-y-1/2 text-[#8c909f]" />

              <input
                value={filterText}
                onChange={(event) =>
                  setFilterText(
                    event.target.value
                  )
                }
                placeholder="Filter IP / Process / PID..."
                className="bg-[#10131a] border border-[#424754] rounded pl-8 pr-3 py-1.5 font-mono text-[10px] text-[#e1e2ec] focus:outline-none focus:border-[#adc6ff] w-56 placeholder-[#8c909f]"
              />

            </div>


            {/* FILTERS */}

            <div className="flex gap-1">

              {[
                'ALL',
                'SUSPICIOUS',
                'ANOMALY',
                'NORMAL',
              ].map(
                (filter) => (

                  <button
                    key={filter}
                    onClick={() =>
                      setSelectedStatusFilter(
                        filter
                      )
                    }
                    className={`px-2 py-1.5 rounded font-mono text-[8px] font-bold border ${
                      selectedStatusFilter ===
                      filter
                        ? 'bg-[#adc6ff] text-[#002e6a] border-[#adc6ff]'
                        : 'bg-[#10131a] text-[#c2c6d6] border-[#424754] hover:bg-[#272a31]'
                    }`}
                  >
                    {filter}
                  </button>

                )
              )}

            </div>

          </div>

        </div>


        {/* TABLE */}

        <div className="overflow-auto max-h-[560px]">

          <table className="w-full text-left border-collapse font-mono text-[10px]">


            <thead className="sticky top-0 bg-[#32353c] border-b border-[#424754] z-10 text-[#c2c6d6] uppercase font-bold tracking-wider">

              <tr>

                <th className="p-2.5 pl-4">
                  TIME (UTC)
                </th>

                <th className="p-2.5">
                  PROCESS
                </th>

                <th className="p-2.5">
                  PID
                </th>

                <th className="p-2.5">
                  LOCAL ADDRESS
                </th>

                <th className="p-2.5">
                  REMOTE ADDRESS
                </th>

                <th className="p-2.5">
                  STATUS
                </th>

                <th className="p-2.5 pr-4 text-right">
                  INDICATOR
                </th>

              </tr>

            </thead>


            <tbody className="divide-y divide-[#424754]/30">


              {filteredConnections.length === 0 ? (

                <tr>

                  <td
                    colSpan={7}
                    className="p-10 text-center text-[#8c909f]"
                  >
                    No network events match the current filter.
                  </td>

                </tr>

              ) : (

                filteredConnections.map(
                  (connection) => {

                    const indicator =
                      (
                        connection.indicator ||
                        ''
                      ).toLowerCase();


                    const isRepeated =
                      indicator ===
                        'repeated_connection_to_endpoint' ||
                      indicator ===
                        'repeated_connection';


                    const isEstablished =
                      connection.status ===
                        'ESTABLISHED' ||
                      connection.status ===
                        'ESTAB';


                    return (

                      <tr
                        key={connection.id}
                        onClick={() =>
                          inspectConnection(
                            connection
                          )
                        }
                        className={`cursor-pointer hover:bg-[#272a31] transition-colors ${
                          isRepeated
                            ? 'bg-[#93000a]/15 border-l-2 border-l-[#ffb4ab]'
                            : ''
                        }`}
                      >


                        {/* TIME */}

                        <td className="p-2.5 pl-4 text-[#c2c6d6] whitespace-nowrap">
                          {connection.time}
                        </td>


                        {/* PROCESS */}

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
                              {connection.process ||
                                'Unknown'}
                            </span>

                          </div>

                        </td>


                        {/* PID */}

                        <td className="p-2.5 text-[#c2c6d6]">
                          {connection.pid ??
                            '—'}
                        </td>


                        {/* LOCAL */}

                        <td className="p-2.5 text-[#e1e2ec] whitespace-nowrap">
                          {connection.localAddress ||
                            'Unknown'}
                        </td>


                        {/* REMOTE */}

                        <td className="p-2.5 text-[#e1e2ec] font-bold whitespace-nowrap">
                          {connection.remoteAddress ||
                            'Unknown'}
                        </td>


                        {/* STATUS */}

                        <td className="p-2.5">

                          {isEstablished ? (

                            <span className="text-[#4edea3] flex items-center gap-1.5">

                              <span className="w-1.5 h-1.5 rounded-full bg-[#4edea3]" />

                              ESTABLISHED

                            </span>

                          ) : (

                            <span className="text-[#c2c6d6]">
                              {connection.status ||
                                'UNKNOWN'}
                            </span>

                          )}

                        </td>


                        {/* INDICATOR */}

                        <td className="p-2.5 pr-4 text-right">

                          {isRepeated ? (

                            <span className="inline-block px-2 py-0.5 border border-[#ffb4ab] bg-[#93000a]/40 rounded text-[#ffb4ab] font-bold text-[8px]">
                              REPEATED ENDPOINT
                            </span>

                          ) : (

                            <span className="inline-block px-2 py-0.5 border border-[#424754] bg-[#10131a] rounded text-[#c2c6d6] text-[8px]">
                              {connection.indicator ||
                                'OBSERVED'}
                            </span>

                          )}

                        </td>

                      </tr>

                    );

                  }
                )

              )}

            </tbody>

          </table>

        </div>

      </div>


      {/* ======================================================
          SOCKET INSPECTION
          ====================================================== */}

      {selectedConnection && (

        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">


          <div className="bg-[#191b23] border border-[#424754] rounded-lg max-w-md w-full p-5 shadow-2xl font-mono text-[11px]">


            <div className="flex items-center justify-between border-b border-[#424754] pb-3 mb-4">

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

                <span className="text-[#e1e2ec]">
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

                <span className="text-[#adc6ff]">
                  {selectedConnection.localAddress ||
                    'Unknown'}
                </span>

              </div>


              <div className="flex justify-between gap-4">

                <span className="text-[#8c909f]">
                  REMOTE
                </span>

                <span className="text-[#adc6ff]">
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


            <div className="border-t border-[#424754] mt-4 pt-3 text-[#8c909f] text-[9px] leading-relaxed">

              Network indicators are behavioral evidence.
              A repeated endpoint does not independently
              prove command-and-control or ransomware activity.

            </div>


            <div className="flex gap-2 mt-4">


              <button
                onClick={() => {

                  const process =
                    processes.find(
                      (item) =>
                        item.pid ===
                        selectedConnection.pid
                    );


                  if (process) {

                    setSelectedProcess(
                      process
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
