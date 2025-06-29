import { ExtractAttribute, ExtractRateQuery, SearchResult } from '@/typings/searchType';
import axios from 'axios'

export async function getInfo(q: string): Promise<SearchResult> {
    const res = await axios.get<SearchResult>('/api/search', {
        params: { q }
    })
    return res.data
}

export async function subRate(query: string, rate: number) {
    const res = await axios.post('/api/rate', {
        query,
        rate
    })
    return res.data
}

export async function getExtractedInfo(doc_id: string): Promise<ExtractAttribute> {
    const res = await axios.get(`/api/extract`, {
        params: { url: doc_id }
    })
    return res.data
}

export async function subExtractRate(query: ExtractRateQuery) {
    const res = await axios.post('/api/extract/rate', query)
    return res.data
}