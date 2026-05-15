// Deterministic mock data for the Meta Ads dashboard.
// All numbers are illustrative.

const OBJECTIVES = ["Conversions", "Traffic", "Awareness", "Engagement"];
const STATUSES = ["active", "active", "active", "paused", "ended"];

// Seeded pseudo-random so the dashboard renders consistently.
function mulberry32(seed) {
  return function () {
    let t = (seed += 0x6d2b79f5);
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function buildDailySeries(days) {
  const rand = mulberry32(42);
  const today = new Date();
  const out = [];
  for (let i = days - 1; i >= 0; i--) {
    const d = new Date(today);
    d.setDate(today.getDate() - i);
    const weekday = d.getDay();
    const weekendFactor = weekday === 0 || weekday === 6 ? 0.85 : 1.05;
    const trend = 1 + (days - i) * 0.004;
    const noise = 0.85 + rand() * 0.3;
    const spend = Math.round(1850 * weekendFactor * trend * noise);
    const revenue = Math.round(spend * (2.2 + rand() * 1.3));
    const impressions = Math.round(spend * (380 + rand() * 120));
    const clicks = Math.round(impressions * (0.011 + rand() * 0.005));
    const conversions = Math.round(clicks * (0.04 + rand() * 0.02));
    out.push({
      date: d.toISOString().slice(0, 10),
      spend,
      revenue,
      impressions,
      clicks,
      conversions,
    });
  }
  return out;
}

const CAMPAIGNS = [
  { name: "Spring Sale — Prospecting", objective: "Conversions", status: "active",  spend: 18420, impressions: 6_240_000, clicks: 78_300, conversions: 2410, revenue: 71_300 },
  { name: "Retargeting — Cart Abandon", objective: "Conversions", status: "active", spend: 9_240,  impressions: 1_980_000, clicks: 41_200, conversions: 1860, revenue: 58_900 },
  { name: "Lookalike 1% — US",           objective: "Conversions", status: "active", spend: 14_120, impressions: 4_320_000, clicks: 52_400, conversions: 1480, revenue: 42_100 },
  { name: "Brand Awareness — Reels",     objective: "Awareness",   status: "active", spend: 7_800,  impressions: 9_140_000, clicks: 31_600, conversions: 210,  revenue: 5_300  },
  { name: "Engagement — UGC Videos",     objective: "Engagement",  status: "active", spend: 5_410,  impressions: 3_210_000, clicks: 24_800, conversions: 320,  revenue: 9_800  },
  { name: "Traffic — Blog Funnel",       objective: "Traffic",     status: "paused", spend: 3_120,  impressions: 1_540_000, clicks: 28_900, conversions: 140,  revenue: 3_200  },
  { name: "Holiday Teaser — EU",         objective: "Awareness",   status: "ended",  spend: 11_300, impressions: 7_810_000, clicks: 36_200, conversions: 480,  revenue: 12_900 },
  { name: "Catalog Sales — DPA",         objective: "Conversions", status: "active", spend: 16_980, impressions: 5_640_000, clicks: 64_700, conversions: 2120, revenue: 65_800 },
  { name: "Welcome Series — New Visit",  objective: "Traffic",     status: "active", spend: 4_280,  impressions: 1_870_000, clicks: 33_500, conversions: 290,  revenue: 6_400  },
  { name: "VIP Reactivation",            objective: "Conversions", status: "paused", spend: 2_910,  impressions: 940_000,   clicks: 12_400, conversions: 410,  revenue: 14_200 },
];

const TOP_ADS = [
  { id: "ad-001", title: "Spring Sale 30% Off", campaign: "Spring Sale — Prospecting", format: "Video",   spend: 6420, ctr: 2.31, roas: 4.12, color: "#4f7cff,#7c5cff" },
  { id: "ad-002", title: "Your Cart is Waiting", campaign: "Retargeting — Cart Abandon", format: "Carousel", spend: 3120, ctr: 3.85, roas: 6.41, color: "#ff7a59,#ff4f7c" },
  { id: "ad-003", title: "Why Customers Love Us", campaign: "Engagement — UGC Videos", format: "Reels",   spend: 2080, ctr: 2.07, roas: 1.81, color: "#2ecc71,#1abc9c" },
  { id: "ad-004", title: "Best Sellers 2026",     campaign: "Catalog Sales — DPA",      format: "Catalog", spend: 5870, ctr: 1.94, roas: 3.87, color: "#f5a623,#ff6b6b" },
];

const PLACEMENTS = [
  { name: "Feed",     spend: 38420, conversions: 5320 },
  { name: "Stories",  spend: 19280, conversions: 1840 },
  { name: "Reels",    spend: 22140, conversions: 2210 },
  { name: "Marketplace", spend: 6_120, conversions: 410 },
  { name: "Audience Network", spend: 4_980, conversions: 290 },
];

const AGE_BUCKETS = ["18-24", "25-34", "35-44", "45-54", "55-64", "65+"];
const AGE_GENDER = {
  male:   [1820, 4210, 3520, 2110, 1180, 540],
  female: [2410, 5320, 4180, 2480, 1320, 610],
};

window.MOCK = {
  OBJECTIVES,
  STATUSES,
  buildDailySeries,
  CAMPAIGNS,
  TOP_ADS,
  PLACEMENTS,
  AGE_BUCKETS,
  AGE_GENDER,
};
