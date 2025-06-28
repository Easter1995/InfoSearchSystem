export interface SearchInfo {
    director: string,
    match: string,
    rate: string,
    sim: number,
    stars: string,
    summary: string,
    title: string,
    url: string,
    writers: string
}

export interface SearchResult {
    corrections: Array<string>,
    has_corrections: Boolean,
    results: Array<SearchInfo>,
    timestamp: string,
    total: number
}

export interface ExtractBasicInfo {
    title: string,
    rate: string,
    director: string,
    writers: string,
    stars: string,
    summary: string,
    url: string
}

export interface ExtractExtraInfo {
    keywords: Array<string>,
    persons: Array<string>,
    organizations: Array<string>,
    locations: Array<string>
}

export interface ExtractAttribute {
    doc_id: string,
    // basic_info: ExtractBasicInfo,
    extracted_info: ExtractExtraInfo,
    success: boolean
}

export interface ExtractSearchInfo {
    doc_id: string,
    match_score: number,
}
export interface ExtractSearchResult {
    query: string,
    type: string,
    total: number,
}