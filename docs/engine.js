/** Client-side club matcher engine for GitHub Pages (no Python server). */
const ClubMatcher = (() => {
  const NONE_ID = "__none__";
  let CFG = {};
  let parentMap = {};
  let tagTree = {};
  let topLevel = {};
  let clubs = [];
  let tagList = [];

  function displayName(tag) {
    const special = { AI: "AI", STEM: "STEM", anime: "Anime" };
    if (special[tag]) return special[tag];
    return tag.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
  }

  function ancestorChain(tag) {
    const chain = [tag];
    let current = tag;
    while (parentMap[current] != null) {
      current = parentMap[current];
      chain.push(current);
    }
    return chain;
  }

  function hierarchyDistance(a, b) {
    if (a === b) return 0;
    const chainA = ancestorChain(a);
    const chainB = ancestorChain(b);
    let best = null;
    chainA.forEach((ancestor, i) => {
      const j = chainB.indexOf(ancestor);
      if (j >= 0) {
        const d = i + j;
        if (d <= 2 && (best === null || d < best)) best = d;
      }
    });
    return best;
  }

  function hierarchyCoefficient(a, b) {
    const d = hierarchyDistance(a, b);
    if (d === null) return 0;
    if (d === 0) return CFG.HIERARCHY_EXACT;
    if (d === 1) return CFG.HIERARCHY_PARENT_CHILD;
    if (d === 2) return CFG.HIERARCHY_GRANDRELATED;
    return 0;
  }

  function pathToTag(tag) {
    const chain = [tag];
    let current = tag;
    while (parentMap[current] != null) {
      current = parentMap[current];
      chain.push(current);
    }
    return chain.reverse();
  }

  function children(tag) {
    let node = tagTree;
    for (const part of pathToTag(tag)) {
      if (!node[part]) return [];
      node = node[part];
    }
    return Object.keys(node);
  }

  function normalizeTag(tag) {
    const lower = tag.trim().replace(/ /g, "_").toLowerCase();
    for (const known of Object.keys(parentMap)) {
      if (known.toLowerCase() === lower) return known;
    }
    return lower;
  }

  function distributeUserWeights(tags) {
    const total = CFG.USER_TAG_POINTS;
    const raw = tags.map((_, i) => tags.length - i);
    const rawSum = raw.reduce((a, b) => a + b, 0);
    const weights = raw.map((w) => Math.round((total * w) / rawSum));
    weights[0] += total - weights.reduce((a, b) => a + b, 0);
    return Object.fromEntries(tags.map((t, i) => [t, weights[i]]));
  }

  function popularityMultiplier(memberCount) {
    for (const [threshold, mult] of CFG.POPULARITY_TIERS) {
      if (memberCount >= threshold) return mult;
    }
    return 1;
  }

  function computeMatchedWeight(userTags, clubTags) {
    let matchedWeight = 0;
    const matches = [];
    for (const [userTag, userWeight] of Object.entries(userTags)) {
      let best = null;
      for (const [clubTag, clubWeight] of Object.entries(clubTags)) {
        const coeff = hierarchyCoefficient(userTag, clubTag);
        if (coeff <= 0) continue;
        const contribution = Math.min(userWeight, clubWeight) * coeff;
        if (!best || contribution > best.contribution) {
          best = { userTag, clubTag, coeff, contribution };
        }
      }
      if (best) {
        matchedWeight += best.contribution;
        matches.push(best);
      }
    }
    return { matchedWeight, matches };
  }

  function matchingTagLabels(matches) {
    const seen = new Set();
    const labels = [];
    [...matches]
      .sort((a, b) => b.contribution - a.contribution)
      .forEach((m) => {
        let label;
        if (m.coeff >= 1) label = displayName(m.userTag);
        else if (m.userTag !== m.clubTag) {
          label = `${displayName(m.userTag)} → ${displayName(m.clubTag)}`;
        } else label = displayName(m.userTag);
        if (!seen.has(label)) {
          seen.add(label);
          labels.push(label);
        }
      });
    return labels;
  }

  function explanation(similarity, matches) {
    const labels = matchingTagLabels(matches);
    if (!labels.length) return "No strong tag overlap with your selected interests.";
    let tagText;
    if (labels.length === 1) tagText = labels[0];
    else if (labels.length === 2) tagText = `${labels[0]} and ${labels[1]}`;
    else tagText = `${labels.slice(0, -1).join(", ")}, and ${labels[labels.length - 1]}`;
    const strength = similarity >= 0.5 ? "strongly" : "moderately";
    return `Matched ${strength} because of ${tagText}.`;
  }

  function filterClubs(blockedSlots) {
    const blocked = new Set(blockedSlots || []);
    return clubs.filter((club) => {
      if (club.member_count <= CFG.MIN_ACTIVE_MEMBER_COUNT) return false;
      const slot = `${club.day}:${club.period}`;
      if (blocked.size && blocked.has(slot)) return false;
      return true;
    });
  }

  function scoreClub(club, userTags) {
    const clubTotal = Object.values(club.tags).reduce((a, b) => a + b, 0) || CFG.CLUB_TAG_POINTS;
    const userTotal = Object.values(userTags).reduce((a, b) => a + b, 0) || CFG.USER_TAG_POINTS;
    const { matchedWeight, matches } = computeMatchedWeight(userTags, club.tags);
    const precision = matchedWeight / clubTotal;
    const recall = matchedWeight / userTotal;
    const similarity =
      CFG.SIMILARITY_PRECISION_WEIGHT * precision + CFG.SIMILARITY_RECALL_WEIGHT * recall;
    const pop = popularityMultiplier(club.member_count);
    const finalScore = similarity * pop;
    return { club, similarity, finalScore, pop, matches };
  }

  function recommend(tagNames, blockedSlots) {
    const normalized = tagNames.map(normalizeTag);
    const userTags = distributeUserWeights(normalized);
    const eligible = filterClubs(blockedSlots);
    const results = eligible
      .map((club) => scoreClub(club, userTags))
      .sort(
        (a, b) =>
          b.finalScore - a.finalScore ||
          b.similarity - a.similarity ||
          a.club.name.localeCompare(b.club.name)
      );

    const above = results.filter((r) => r.finalScore > CFG.MIN_FINAL_SCORE);
    const below = results.filter((r) => r.finalScore <= CFG.MIN_FINAL_SCORE);
    const picked = above.slice(0, CFG.TOP_N_RESULTS);
    if (picked.length < CFG.MIN_RESULTS) {
      picked.push(...below.slice(0, Math.min(CFG.MIN_RESULTS, CFG.TOP_N_RESULTS) - picked.length));
    }
    return picked.slice(0, CFG.TOP_N_RESULTS).map((r) => ({
      name: r.club.name,
      category: r.club.category,
      description: r.club.description,
      member_count: r.club.member_count,
      day: r.club.day,
      period: r.club.period,
      final_score_pct: Math.round(r.finalScore * 1000) / 10,
      above_threshold: r.finalScore > CFG.MIN_FINAL_SCORE,
      matching_tags: matchingTagLabels(r.matches),
      explanation: explanation(r.similarity, r.matches),
    }));
  }

  function emptySession() {
    return {
      phase: "root",
      areas: [],
      area_index: 0,
      branch_queue: [],
      drill_extra: [],
      pending_drill_nodes: [],
    };
  }

  function cloneSession(s) {
    return {
      phase: s.phase,
      areas: [...s.areas],
      area_index: s.area_index,
      branch_queue: [...s.branch_queue],
      drill_extra: [...s.drill_extra],
      pending_drill_nodes: [...(s.pending_drill_nodes || [])],
    };
  }

  function noneOption(label) {
    return { id: NONE_ID, label: `None — use ${label} instead`, tag: null, is_leaf: false, is_none: true };
  }

  function optionForTag(tag) {
    return {
      id: tag,
      label: displayName(tag),
      tag: children(tag).length ? null : tag,
      is_leaf: !children(tag).length,
      is_none: false,
    };
  }

  function drillNode(session) {
    return session.drill_extra.length
      ? session.drill_extra[session.drill_extra.length - 1]
      : session.branch_queue[0];
  }

  function advanceToNextArea(session, tagsAdded) {
    session.area_index += 1;
    session.phase = session.area_index >= session.areas.length ? "complete" : "branches";
    return { session, tags_added: tagsAdded };
  }

  function finishCurrentBranch(session, tagsAdded) {
    session.drill_extra = [];
    session.pending_drill_nodes = [];
    session.branch_queue.shift();
    if (session.branch_queue.length) return { session, tags_added: tagsAdded };
    return advanceToNextArea(session, tagsAdded);
  }

  function startNextPendingDrill(session, tagsAdded) {
    if (session.pending_drill_nodes?.length) {
      session.drill_extra = [session.pending_drill_nodes.shift()];
      return { session, tags_added: tagsAdded };
    }
    return finishCurrentBranch(session, tagsAdded);
  }

  function quizStepFromSession(session) {
    session = session || emptySession();
    if (session.phase === "root") {
      return stepPayload(session, {
        step_id: "root",
        question: "What broad areas interest you? (choose one or more)",
        options: [
          ...Object.entries(topLevel).map(([id, meta]) => ({
            id,
            label: meta.label,
            tag: null,
            is_leaf: false,
            is_none: false,
          })),
          noneOption("nothing from this list"),
        ],
        phase: "root",
      });
    }
    if (session.phase === "branches") {
      const area = session.areas[session.area_index];
      const meta = topLevel[area];
      return stepPayload(session, {
        step_id: `${area}:branches`,
        question: meta.prompt,
        options: [...meta.branches.map(optionForTag), noneOption(meta.label)],
        phase: "branches",
      });
    }
    if (session.phase === "drill") {
      const branch = session.branch_queue[0];
      const node = drillNode(session);
      const parentLabel = displayName(node);
      const question = session.drill_extra.length
        ? `Which ${parentLabel} topics fit you? (choose one or more)`
        : `Which ${displayName(branch)} topics fit you? (choose one or more)`;
      return stepPayload(session, {
        step_id: `drill:${branch}:${session.drill_extra.join("/")}`,
        question,
        options: [...children(node).map(optionForTag), noneOption(parentLabel)],
        none_parent_tag: node,
        phase: "drill",
      });
    }
    return stepPayload(session, {
      step_id: "complete",
      question: "Round complete. Starting a new round…",
      options: [],
      can_continue: false,
      multi_select: false,
      phase: "complete",
    });
  }

  function stepPayload(session, partial) {
    return {
      step_id: partial.step_id,
      question: partial.question,
      multi_select: partial.multi_select !== false,
      can_continue: partial.can_continue !== false,
      phase: partial.phase,
      none_parent_tag: partial.none_parent_tag || null,
      session: cloneSession(session),
      options: partial.options || [],
      tags_added: [],
    };
  }

  function drillContinue(session, selections) {
    const node = drillNode(session);
    const valid = new Set(children(node));
    selections.forEach((sel) => {
      if (!valid.has(sel)) throw new Error(`Invalid selection: ${sel}`);
    });

    const tagsAdded = [];
    const drillDeeper = [];
    selections.forEach((sel) => {
      if (children(sel).length) drillDeeper.push(sel);
      else tagsAdded.push(sel);
    });

    if (drillDeeper.length) {
      session.drill_extra = [drillDeeper[0]];
      session.pending_drill_nodes = [...drillDeeper.slice(1), ...(session.pending_drill_nodes || [])];
      return { session, tags_added: tagsAdded };
    }
    return startNextPendingDrill(session, tagsAdded);
  }

  function quizContinue(session, selections) {
    session = cloneSession(session);
    if (!selections?.length) throw new Error("Select at least one option before continuing.");
    if (selections.includes(NONE_ID) && selections.length > 1) {
      throw new Error('Choose "None" by itself, or pick other options (not both).');
    }

    if (selections.includes(NONE_ID)) {
      if (session.phase === "root") {
        session.phase = "complete";
        return { session, tags_added: [] };
      }
      if (session.phase === "branches") return advanceToNextArea(session, []);
      if (session.phase === "drill") return startNextPendingDrill(session, [drillNode(session)]);
    }

    if (session.phase === "root") {
      session.areas = selections;
      session.area_index = 0;
      session.phase = "branches";
      return { session, tags_added: [] };
    }
    if (session.phase === "branches") {
      session.branch_queue = selections;
      session.drill_extra = [];
      session.pending_drill_nodes = [];
      session.phase = "drill";
      return { session, tags_added: [] };
    }
    if (session.phase === "drill") return drillContinue(session, selections);
    throw new Error("Continue is not available at this step.");
  }

  function handleQuiz(body) {
    const session = body.session || emptySession();
    if (body.action === "restart") return quizStepFromSession(emptySession());
    if (body.action === "status") return quizStepFromSession(session);
    if (body.action === "continue") {
      const { session: next, tags_added } = quizContinue(session, body.selections || []);
      const step = quizStepFromSession(next);
      step.tags_added = tags_added;
      return step;
    }
    throw new Error("Unknown quiz action.");
  }

  async function init(dataBase = "data/") {
    const base = dataBase.endsWith("/") ? dataBase : `${dataBase}/`;
    const [site, clubData] = await Promise.all([
      fetch(`${base}site.json`).then((r) => {
        if (!r.ok) throw new Error("Failed to load site.json");
        return r.json();
      }),
      fetch(`${base}clubs.json`).then((r) => {
        if (!r.ok) throw new Error("Failed to load clubs.json");
        return r.json();
      }),
    ]);
    CFG = site.config;
    parentMap = site.parentMap;
    tagTree = site.tagTree;
    topLevel = site.topLevel;
    tagList = site.tags;
    clubs = clubData;
  }

  function getTags() {
    return { tags: tagList, max_tags: CFG.MAX_USER_TAGS };
  }

  function recommendPayload(tagNames, blockedSlots) {
    const results = recommend(tagNames, blockedSlots);
    const above = results.filter((r) => r.above_threshold).length;
    return {
      count: results.length,
      above_threshold: above,
      min_results: CFG.MIN_RESULTS,
      tags: tagNames,
      blocked_slots: blockedSlots,
      results,
    };
  }

  return { init, getTags, recommendPayload, quizStepFromSession, handleQuiz, emptySession };
})();

window.ClubMatcher = ClubMatcher;
