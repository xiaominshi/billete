'use strict';

// ── Built-in airport name map (IATA code → Chinese name) ─────────────────
// Extend this object to add more airports; user overrides are merged at runtime
const BUILTIN_AIRPORTS = {
  // ── 中国大陆 ──
  PEK:'北京首都', PKX:'北京大兴', SHA:'上海虹桥', PVG:'上海浦东',
  CAN:'广州白云', SZX:'深圳宝安', CTU:'成都天府', TFU:'成都天府',
  XIY:'西安咸阳', WUH:'武汉天河', KMG:'昆明长水', CSX:'长沙黄花',
  HGH:'杭州萧山', NKG:'南京禄口', TSN:'天津滨海', DLC:'大连周水子',
  TAO:'青岛胶东', TNA:'济南遥墙', HRB:'哈尔滨太平', SHE:'沈阳桃仙',
  URC:'乌鲁木齐地窝堡', XMN:'厦门高崎', FOC:'福州长乐', KWE:'贵阳龙洞堡',
  NNG:'南宁吴圩', HAK:'海口美兰', SYX:'三亚凤凰', LHW:'兰州中川',
  INC:'银川河东', TYN:'太原武宿', CGQ:'长春龙嘉', HET:'呼和浩特白塔',
  ZHA:'湛江', WNZ:'温州龙湾', NGB:'宁波栎社', CGD:'常德桃花源',
  MXZ:'梅州', YNT:'烟台蓬莱', NTG:'南通兴东', WEH:'威海大水泊',
  CZX:'常州奔牛', YIW:'义乌', LYI:'临沂', ZUH:'珠海金湾',
  SWA:'揭揭汕', HUZ:'惠州平潭', MIG:'绵阳南郊', KHN:'南昌昌北',
  HFE:'合肥新桥', IQN:'庆阳', LXA:'拉萨贡嘎', YBP:'宜宾五粮液',
  // ── 港澳台 ──
  HKG:'香港', MFM:'澳门', TPE:'台北桃园', TSA:'台北松山', KHH:'高雄',
  // ── 日韩 ──
  NRT:'东京成田', HND:'东京羽田', KIX:'大阪关西', ITM:'大阪伊丹',
  NGO:'名古屋', FUK:'福冈', SPK:'札幌新千岁', CTS:'札幌新千岁',
  ICN:'首尔仁川', GMP:'首尔金浦', PUS:'釜山',
  // ── 东南亚 ──
  BKK:'曼谷素万那普', DMK:'曼谷廊曼', HKT:'普吉', CNX:'清迈',
  SIN:'新加坡樟宜', KUL:'吉隆坡', MNL:'马尼拉', CEB:'宿务',
  DPS:'巴厘岛', CGK:'雅加达苏加诺', HAN:'河内', SGN:'胡志明市',
  DAD:'岘港', RGN:'仰光', PNH:'金边', REP:'暹粒',
  VTE:'万象', ULN:'乌兰巴托',
  // ── 南亚/中亚 ──
  DEL:'新德里', BOM:'孟买', MAA:'金奈', BLR:'班加罗尔',
  CMB:'科伦坡', KTM:'加德满都', DAC:'达卡',
  ALA:'阿拉木图', TAS:'塔什干', OSS:'奥什',
  // ── 中东 ──
  DXB:'迪拜', AUH:'阿布扎比', DOH:'多哈', RUH:'利雅得',
  JED:'吉达', BAH:'巴林', MCT:'马斯喀特', KWI:'科威特',
  CAI:'开罗', ADD:'亚的斯亚贝巴', NBO:'内罗毕',
  // ── 欧洲 ──
  LHR:'伦敦希思罗', LGW:'伦敦盖特威克', STN:'伦敦斯坦斯特德',
  CDG:'巴黎戴高乐', ORY:'巴黎奥利',
  FRA:'法兰克福', MUC:'慕尼黑', DUS:'杜塞尔多夫', BER:'柏林',
  AMS:'阿姆斯特丹', BRU:'布鲁塞尔', ZRH:'苏黎世', GVA:'日内瓦',
  VIE:'维也纳', PRG:'布拉格', WAW:'华沙', BUD:'布达佩斯',
  FCO:'罗马菲乌米奇诺', MXP:'米兰马尔彭萨', LIN:'米兰利纳特',
  BCN:'巴塞罗那', MAD:'马德里', LIS:'里斯本', OPO:'波尔图',
  ATH:'雅典', IST:'伊斯坦布尔', SAW:'伊斯坦布尔萨比哈',
  SVO:'莫斯科谢列梅捷沃', DME:'莫斯科多莫杰多沃', LED:'圣彼得堡',
  CPH:'哥本哈根', ARN:'斯德哥尔摩', HEL:'赫尔辛基', OSL:'奥斯陆',
  DUB:'都柏林', EDI:'爱丁堡', MAN:'曼彻斯特',
  // ── 北美 ──
  JFK:'纽约肯尼迪', EWR:'纽约纽瓦克', LGA:'纽约拉瓜迪亚',
  LAX:'洛杉矶', SFO:'旧金山', SEA:'西雅图', ORD:'芝加哥奥黑尔',
  MDW:'芝加哥中途', DFW:'达拉斯', IAH:'休斯顿', MIA:'迈阿密',
  ATL:'亚特兰大', BOS:'波士顿', LAS:'拉斯维加斯', DEN:'丹佛',
  YYZ:'多伦多皮尔逊', YVR:'温哥华', YUL:'蒙特利尔',
  MEX:'墨西哥城', GDL:'瓜达拉哈拉', MTY:'蒙特雷',
  // ── 拉丁美洲 ──
  EZE:'布宜诺斯艾利斯', AEP:'布宜诺斯艾利斯豪尔赫',
  GRU:'圣保罗瓜鲁柳斯', GIG:'里约热内卢加利昂',
  SCL:'圣地亚哥', LIM:'利马', BOG:'波哥大', MDE:'麦德林',
  UIO:'基多', GYE:'瓜亚基尔', ASU:'亚松森',
  MVD:'蒙得维的亚', HAV:'哈瓦那', PTY:'巴拿马城',
  SJO:'圣何塞', SAL:'圣萨尔瓦多', TGU:'特古西加尔巴',
  MGA:'马那瓜', GUA:'危地马拉城',
  // ── 大洋洲 ──
  SYD:'悉尼', MEL:'墨尔本', BNE:'布里斯班', PER:'珀斯', ADL:'阿德莱德',
  AKL:'奥克兰', CHC:'基督城',
  // ── 非洲 ──
  JNB:'约翰内斯堡', CPT:'开普敦', LOS:'拉各斯', ACC:'阿克拉',
};

// Timezone map for duration calculation (IATA code → IANA tz name)
// Only major airports included; falls back to UTC if not found
const AIRPORT_TZ = {
  PEK:'Asia/Shanghai', PKX:'Asia/Shanghai', PVG:'Asia/Shanghai', SHA:'Asia/Shanghai',
  CAN:'Asia/Shanghai', SZX:'Asia/Shanghai', CTU:'Asia/Shanghai', TFU:'Asia/Shanghai',
  XIY:'Asia/Shanghai', WUH:'Asia/Shanghai', KMG:'Asia/Shanghai', HGH:'Asia/Shanghai',
  NKG:'Asia/Shanghai', TSN:'Asia/Shanghai', DLC:'Asia/Shanghai', HRB:'Asia/Shanghai',
  SHE:'Asia/Shanghai', TAO:'Asia/Shanghai', XMN:'Asia/Shanghai', URC:'Asia/Urumqi',
  HKG:'Asia/Hong_Kong', MFM:'Asia/Macau', TPE:'Asia/Taipei', TSA:'Asia/Taipei',
  NRT:'Asia/Tokyo', HND:'Asia/Tokyo', KIX:'Asia/Tokyo', FUK:'Asia/Tokyo',
  CTS:'Asia/Tokyo', NGO:'Asia/Tokyo',
  ICN:'Asia/Seoul', GMP:'Asia/Seoul', PUS:'Asia/Seoul',
  SIN:'Asia/Singapore', KUL:'Asia/Kuala_Lumpur',
  BKK:'Asia/Bangkok', DMK:'Asia/Bangkok', HKT:'Asia/Bangkok', CNX:'Asia/Bangkok',
  SGN:'Asia/Ho_Chi_Minh', HAN:'Asia/Bangkok',
  DPS:'Asia/Makassar', CGK:'Asia/Jakarta',
  MNL:'Asia/Manila', ULN:'Asia/Ulaanbaatar',
  DEL:'Asia/Kolkata', BOM:'Asia/Kolkata',
  DXB:'Asia/Dubai', AUH:'Asia/Dubai', DOH:'Asia/Qatar', RUH:'Asia/Riyadh',
  LHR:'Europe/London', LGW:'Europe/London', CDG:'Europe/Paris', ORY:'Europe/Paris',
  FRA:'Europe/Berlin', MUC:'Europe/Berlin', AMS:'Europe/Amsterdam',
  MAD:'Europe/Madrid', BCN:'Europe/Madrid', LIS:'Europe/Lisbon',
  FCO:'Europe/Rome', MXP:'Europe/Rome', ZRH:'Europe/Zurich',
  IST:'Europe/Istanbul', SVO:'Europe/Moscow', DME:'Europe/Moscow',
  JFK:'America/New_York', EWR:'America/New_York', LGA:'America/New_York',
  LAX:'America/Los_Angeles', SFO:'America/Los_Angeles',
  ORD:'America/Chicago', DFW:'America/Chicago',
  YYZ:'America/Toronto', YVR:'America/Vancouver',
  MEX:'America/Mexico_City',
  EZE:'America/Argentina/Buenos_Aires', GRU:'America/Sao_Paulo',
  SCL:'America/Santiago', LIM:'America/Lima', BOG:'America/Bogota',
  SYD:'Australia/Sydney', MEL:'Australia/Melbourne',
  AKL:'Pacific/Auckland',
};

// ── Helper: get timezone offset in minutes for a date in a given IANA tz ──
function getTzOffsetMinutes(iataCode, date) {
  const tz = AIRPORT_TZ[iataCode] || 'UTC';
  try {
    // Use Intl to get the local time string, then parse offset
    const fmt = new Intl.DateTimeFormat('en-US', {
      timeZone: tz,
      hour: '2-digit', minute: '2-digit', hour12: false,
      year: 'numeric', month: '2-digit', day: '2-digit'
    });
    const parts = fmt.formatToParts(date);
    const get = (t) => parseInt(parts.find(p => p.type === t).value);
    const tzLocal = new Date(get('year'), get('month') - 1, get('day'), get('hour'), get('minute'));
    return (tzLocal - date) / 60000; // diff in minutes (approximation for DST)
  } catch {
    return 0;
  }
}

// ── Main Logic class ────────────────────────────────────────────────────────
class BilleteLogic {
  constructor(customAirports = {}) {
    this.airportMap = Object.assign({}, BUILTIN_AIRPORTS, customAirports);
    this.passengers = [];
    this.flights = [];
    this.layovers = [];
    this.faPaxCount = 0;
    const now = new Date();
    this.currentYear = now.getFullYear();
    this.currentRealMonth = now.getMonth() + 1; // 1-12
    this.lastMonth = null;
  }

  // ── Airport name resolution ──────────────────────────────────────────────
  resolveAirport(code) {
    code = code.toUpperCase();
    return this.airportMap[code] || code;
  }

  // ── Month utilities ──────────────────────────────────────────────────────
  static MONTHS = ['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC'];

  containMonth(text) {
    return BilleteLogic.MONTHS.some(m => text.includes(m));
  }

  getMonthNum(monthStr) {
    const idx = BilleteLogic.MONTHS.indexOf(monthStr.toUpperCase());
    return idx >= 0 ? String(idx + 1).padStart(2, '0') : '-1';
  }

  // ── Line merging (replicate Python logic) ──────────────────────────────
  mergeLinesWithoutSeqNum(text) {
    text = text.replace(/\r\n/g, '\n').replace(/\r/g, '\n');
    const lines = text.split('\n');
    const output = [];
    let prevLine = null;

    for (let line of lines) {
      line = line.trim();
      if (!line) continue;

      let isNewLine = false;
      if (/^\d+(\.|\s)/.test(line))            isNewLine = true;
      else if (line.includes('SSR') || line.includes('FA PAX')) isNewLine = true;
      else if (this.containMonth(line))         isNewLine = true;

      // Continuation of FA PAX / SSR lines
      if (prevLine && (prevLine.includes('FA PAX') || prevLine.includes('SSR'))) {
        if (!line.includes('FA PAX') && !line.includes('SSR')) {
          if (/\/[SP]\d/.test(line) || line.includes('/ET')) {
            isNewLine = false;
          }
        }
      }

      if (isNewLine) {
        if (prevLine !== null) output.push(prevLine);
        prevLine = line;
      } else {
        prevLine = prevLine !== null ? prevLine + ' ' + line : line;
      }
    }
    if (prevLine !== null) output.push(prevLine);
    return output.join('\n');
  }

  // ── Parse passengers ────────────────────────────────────────────────────
  parsePassengers(line) {
    const parts = line.split('.');
    for (let i = 1; i < parts.length; i++) {
      const pName = parts[i].replace(/\d+/g, '').trim();
      if (pName) {
        this.passengers.push({
          name: pName,
          id: `P${this.passengers.length + 1}`,
          passport: '',
          ticket: ''
        });
      }
    }
  }

  // ── Parse SSR DOCS (passport) ────────────────────────────────────────────
  // Handles format: SSR DOCS CZ HK1 P/CHN/EQ5145644/CHN/21MAR98/M/09FEB36/SHI/XIAOMIN/P2
  // The passport data may be split across merged tokens (line continuation), so we
  // join all tokens from P/ onwards and compact spaces out.
  parseSsrDocs(parts) {
    try {
      const fullLine = parts.join(' ');
      const pIdx = fullLine.indexOf('P/');
      if (pIdx === -1) return;

      // Everything from P/ onward, spaces removed (handles split continuation lines)
      const compact = fullLine.slice(pIdx).replace(/\s+/g, '');
      // compact looks like: P/CHN/EQ5145644/CHN/21MAR98/M/09FEB36/SHI/XIAOMIN/P2

      // Extract passport number: 3rd slash-delimited field
      const passMatch = compact.match(/^P\/[A-Z]{3}\/([A-Z0-9]+)\//);
      if (!passMatch) return;
      const passport = passMatch[1];

      // Find passenger reference /P1 or /P2 at end
      const paxMatch = compact.match(/\/P(\d+)$/);
      let paxIdx;
      if (paxMatch) {
        paxIdx = parseInt(paxMatch[1]) - 1;
      } else {
        // No explicit reference: assign to first passenger without passport
        paxIdx = this.passengers.findIndex(p => !p.passport);
      }

      if (paxIdx >= 0 && paxIdx < this.passengers.length) {
        this.passengers[paxIdx].passport = passport;
      }
    } catch (e) { /* ignore */ }
  }

  // ── Parse FA PAX (ticket numbers) ───────────────────────────────────────
  parseFaPax(parts) {
    try {
      const fullLine = parts.join(' ');
      const ticketMatch = fullLine.match(/(\d{3}-\d{10})/);
      if (ticketMatch) {
        const ticketNum = ticketMatch[1];
        this.faPaxCount++;

        const paxMatch = fullLine.match(/\/P(\d+)/);
        if (paxMatch) {
          const pIdx = parseInt(paxMatch[1]) - 1;
          if (pIdx >= 0 && pIdx < this.passengers.length) {
            this.passengers[pIdx].ticket = ticketNum;
          }
        } else {
          // Sequential fallback
          const pIdx = this.faPaxCount - 1;
          if (pIdx >= 0 && pIdx < this.passengers.length) {
            this.passengers[pIdx].ticket = ticketNum;
          }
        }
      }
    } catch (e) { /* ignore */ }
  }

  // ── Parse flight line ────────────────────────────────────────────────────
  parseFlight(parts) {
    try {
      const dateIdx = parts.findIndex(p => this.containMonth(p));
      if (dateIdx === -1) return;

      const flightIdRaw = (parts[1] || '') + (parts[2] || '');
      const flightMatch = flightIdRaw.match(/^([A-Z0-9]{2})(\d{3,4})/);
      const flightId = flightMatch ? flightMatch[1] + flightMatch[2] : flightIdRaw;

      const dateStr = parts[dateIdx];
      const oriDesIdx = dateIdx + 2;
      if (oriDesIdx >= parts.length) return;

      const oriDes = parts[oriDesIdx];
      const ori = oriDes.slice(0, 3);
      const des = oriDes.slice(3);

      const oriName = this.resolveAirport(ori);
      const desName = this.resolveAirport(des);

      // Find all HHMM or HHMM+N time tokens after the origin/dest
      const timesFound = [];
      for (let i = oriDesIdx + 1; i < parts.length; i++) {
        const p = parts[i];
        if (/^\d{4}$/.test(p) || /^\d{4}\+\d$/.test(p)) timesFound.push(p);
      }
      if (timesFound.length < 2) return;

      const startRaw = timesFound[timesFound.length - 2];
      let endRaw   = timesFound[timesFound.length - 1];
      const nextDay = endRaw.includes('+');
      if (nextDay) endRaw = endRaw.split('+')[0];

      const startFmt = `${startRaw.slice(0, 2)}:${startRaw.slice(2)}`;
      const endFmt   = `${endRaw.slice(0, 2)}:${endRaw.slice(2)}`;

      const day = dateStr.slice(0, 2);
      const monthStr = dateStr.slice(2);
      const month = this.getMonthNum(monthStr);
      const monthInt = parseInt(month);

      // Year tracking
      let yearToUse;
      if (this.lastMonth === null) {
        this.lastMonth = monthInt;
        yearToUse = this.currentYear;
      } else {
        if (monthInt < this.lastMonth) this.currentYear++;
        this.lastMonth = monthInt;
        yearToUse = this.currentYear;
      }

      // Duration calculation (timezone-aware via Intl)
      let durationFmt = '--';
      let arrivalDateFmt = `${month}-${day}`;
      try {
        const sh = parseInt(startRaw.slice(0, 2)), sm = parseInt(startRaw.slice(2));
        const eh = parseInt(endRaw.slice(0, 2)),   em = parseInt(endRaw.slice(2));
        const dayInt = parseInt(day);

        const dtStart = new Date(yearToUse, monthInt - 1, dayInt, sh, sm);
        let   dtEnd   = new Date(yearToUse, monthInt - 1, dayInt, eh, em);
        if (nextDay) dtEnd = new Date(dtEnd.getTime() + 86400000);

        // Apply tz offsets to get UTC, then diff
        const offsetStart = getTzOffsetMinutes(ori, dtStart); // local - UTC in min
        const offsetEnd   = getTzOffsetMinutes(des, dtEnd);
        const utcStart = dtStart.getTime() - offsetStart * 60000;
        const utcEnd   = dtEnd.getTime()   - offsetEnd   * 60000;
        const diffMin  = Math.round((utcEnd - utcStart) / 60000);
        if (diffMin > 0) {
          durationFmt = `${Math.floor(diffMin / 60)}小时${diffMin % 60}分`;
        }

        arrivalDateFmt = `${String(dtEnd.getMonth() + 1).padStart(2,'0')}-${String(dtEnd.getDate()).padStart(2,'0')}`;
      } catch (e) { /* fallback already set */ }

      this.flights.push({
        id: flightId,
        origin: oriName, originCode: ori,
        dest: desName,   destCode: des,
        start: startFmt, end: endFmt,
        month, day, year: yearToUse,
        nextDay,
        rawStart: startRaw, rawEnd: endRaw,
        duration: durationFmt,
        arrivalDate: arrivalDateFmt
      });
    } catch (e) { /* ignore */ }
  }

  // ── Calculate layovers ───────────────────────────────────────────────────
  calculateLayovers() {
    this.layovers = [];
    for (let i = 1; i < this.flights.length; i++) {
      const prev = this.flights[i - 1];
      const curr = this.flights[i];
      try {
        const prevDt = new Date(
          parseInt(prev.year), parseInt(prev.month) - 1, parseInt(prev.day),
          parseInt(prev.rawEnd.slice(0, 2)), parseInt(prev.rawEnd.slice(2))
        );
        if (prev.nextDay) prevDt.setDate(prevDt.getDate() + 1);

        const currDt = new Date(
          parseInt(curr.year), parseInt(curr.month) - 1, parseInt(curr.day),
          parseInt(curr.rawStart.slice(0, 2)), parseInt(curr.rawStart.slice(2))
        );

        const diffMin = Math.round((currDt - prevDt) / 60000);
        const hours   = Math.floor(Math.abs(diffMin) / 60);
        const minutes = Math.abs(diffMin) % 60;

        if (hours >= 72) {
          curr.isReturn = true;
          this.layovers.push({ type: 'return_split', flightIndex: i });
        } else {
          this.layovers.push({
            type: 'layover', place: prev.dest,
            hours, minutes, flightIndex: i
          });
        }
      } catch (e) { /* ignore */ }
    }
  }

  // ── Detect format type ──────────────────────────────────────────────────
  // Condensed / name-list format: "  1 SMITH/JOHN  CZ 378 Z 23MAY MADCAN 2 8RXWX6"
  // Each line has passenger name + flight on the same row (no separate pax/flight lines)
  static CONDENSED_LINE_RE = /^\s*\d+\s+([A-Z]+\/[A-Z]+(?:\s+[A-Z]+)?)\s+([A-Z0-9]{2})\s+(\d{1,4})\s+[A-Z]\s+(\d{2}[A-Z]{3})\s+([A-Z]{6})/;
  static COMMAND_LINE_RE   = /^[A-Z]{2,}[\/\s]/;   // e.g. RT/SHI/XIAOMIN, ET, IG, SS...

  isCondensedFormat(lines) {
    let hits = 0;
    for (const line of lines) {
      if (BilleteLogic.CONDENSED_LINE_RE.test(line)) hits++;
    }
    return hits > 0;
  }

  // ── Parse one condensed line ─────────────────────────────────────────────
  parseCondensedLine(line) {
    const m = line.match(BilleteLogic.CONDENSED_LINE_RE);
    if (!m) return;
    const [, nameRaw, airline, fltNum, dateStr, oriDes] = m;

    // Skip lines with no itinerary
    if (line.toUpperCase().includes('NO ACTIVE')) return;

    const name = nameRaw.trim();
    const flightId = airline + fltNum;

    const day      = dateStr.slice(0, 2);
    const monthStr = dateStr.slice(2);
    const month    = this.getMonthNum(monthStr);
    const monthInt = parseInt(month);

    let yearToUse;
    if (this.lastMonth === null) {
      this.lastMonth = monthInt;
      yearToUse = this.currentYear;
    } else {
      if (monthInt < this.lastMonth) this.currentYear++;
      this.lastMonth = monthInt;
      yearToUse = this.currentYear;
    }

    const ori = oriDes.slice(0, 3);
    const des = oriDes.slice(3, 6);

    // Add passenger if not already present
    if (!this.passengers.find(p => p.name === name)) {
      this.passengers.push({ name, id: `P${this.passengers.length + 1}`, passport: '', ticket: '' });
    }

    this.flights.push({
      id: flightId,
      origin: this.resolveAirport(ori), originCode: ori,
      dest:   this.resolveAirport(des), destCode: des,
      start: '--:--', end: '--:--',
      month, day, year: yearToUse,
      nextDay: false,
      rawStart: '0000', rawEnd: '0000',
      duration: '', arrivalDate: `${month}-${day}`
    });
  }

  // ── Main process ────────────────────────────────────────────────────────
  process(rawCode) {
    this.passengers = [];
    this.flights    = [];
    this.layovers   = [];
    this.faPaxCount = 0;
    this.lastMonth  = null;

    const now = new Date();
    this.currentYear      = now.getFullYear();
    this.currentRealMonth = now.getMonth() + 1;

    // Strip Amadeus command echo lines (e.g. "RT/SHI/XIAOMIN", "ET", "IG")
    // Commands are single words in ALL-CAPS, often with / or followed by space then more caps
    const strippedCode = rawCode
      .split('\n')
      .filter(line => !BilleteLogic.COMMAND_LINE_RE.test(line.trim()) || line.trim().length < 3)
      .join('\n');

    const cleaned = this.mergeLinesWithoutSeqNum(strippedCode);
    const lines   = cleaned.split('\n');

    // Determine base year from first flight month
    const monthsFound = [];
    for (const line of lines) {
      if (this.containMonth(line) && !line.includes('SSR') && !line.includes('FA')) {
        for (const m of BilleteLogic.MONTHS) {
          if (line.includes(m)) { monthsFound.push(BilleteLogic.MONTHS.indexOf(m) + 1); break; }
        }
      }
    }
    if (monthsFound.length > 0) {
      const firstFlightMonth = monthsFound[0];
      if (this.currentRealMonth >= 9 && firstFlightMonth <= 4) {
        this.currentYear++;
      }
    }

    // ── Detect which format and dispatch ──────────────────────────────────
    if (this.isCondensedFormat(lines)) {
      // Amadeus compact name-list / condensed PNR format
      for (const line of lines) {
        if (this.containMonth(line)) this.parseCondensedLine(line);
      }
    } else {
      // Standard detailed PNR format
      let passengerMode = true;
      for (const line of lines) {
        const parts = line.split(/\s+/);
        if (!parts.length || !parts[0]) continue;

        if (line.includes('.') && passengerMode && !line.includes('SSR') && !line.includes('FA')) {
          if (parts[0].includes('.')) {
            this.parsePassengers(line);
            continue;
          } else {
            passengerMode = false;
          }
        }

        if (line.includes('SSR') && line.includes('DOCS')) {
          this.parseSsrDocs(parts);
        } else if (line.includes('FA') && line.includes('PAX')) {
          this.parseFaPax(parts);
        } else if (this.containMonth(line) && !line.includes('SSR') && !line.includes('FA')) {
          this.parseFlight(parts);
        }
      }
    }

    this.calculateLayovers();

    return {
      text: this.generateText(),
      structured: {
        passengers: this.passengers,
        flights:    this.flights,
        layovers:   this.layovers
      }
    };
  }

  // ── Generate formatted text output ──────────────────────────────────────
  generateText(opts = {}) {
    const handCount  = opts.handCount  ?? 1;
    const handWeight = opts.handWeight ?? 8;
    const packCount  = opts.packCount  ?? 2;
    const packWeight = opts.packWeight ?? 23;

    let res = '';

    for (let i = 0; i < this.passengers.length; i++) {
      const p = this.passengers[i];
      const tkt = p.ticket ? `\n票号: ${p.ticket}` : '';
      res += `乘客${i + 1}: ${p.name}${tkt}\n`;
    }

    if (this.passengers.length) res += '\n';

    for (let i = 0; i < this.flights.length; i++) {
      const f = this.flights[i];

      if (f.isReturn) {
        res += '---------<回程>---------\n';
      }

      if (i === 0 || f.isReturn) {
        res += `【${f.year}年${f.month}月${f.day}日】\n`;
      }

      const layover = this.layovers.find(l => l.flightIndex === i);
      if (layover && layover.type === 'layover' && layover.hours >= 0) {
        res += `${layover.place}停留: ${layover.hours}小时${layover.minutes}分\n`;
      }

      if (f.start === '--:--') {
        res += `${f.origin} → ${f.dest}\n`;
      } else {
        res += `${f.origin}-${f.dest}-->${f.start}-${f.end}`;
        if (f.nextDay) res += '+1';
        if (f.duration && f.duration !== '--') res += `  (飞行${f.duration})`;
        res += '\n';
      }
    }

    if (packCount > 0 || handCount > 0) {
      res += `\n行李: 手提${handCount}件${handWeight}kg / 托运${packCount}件${packWeight}kg`;
    }

    return res.trim();
  }
}
