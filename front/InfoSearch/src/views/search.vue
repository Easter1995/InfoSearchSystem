<script setup lang="ts">
import { getExtractedInfo, getInfo, subExtractRate, subRate } from '@/api/search';
import { ExtractExtraInfo, SearchResult } from '@/typings/searchType';
import { Search } from '@element-plus/icons-vue'
import { ElLoading, ElNotification } from 'element-plus';
import { ref } from 'vue';
import { stemmer } from 'stemmer'

const userInput = ref('')
const userInputSave = ref('')
const userRate = ref(0)
const showContent = ref(false)
const showRate = ref(false)
const rateFixed = ref(false)
const extractRate = ref<Map<string, number>>(new Map<string, number>())
const searchList = ref<SearchResult>({
    results: [],
    corrections: [],
    has_corrections: false,
    timestamp: '',
    total: 0
})

const extractedInfoList = ref<Map<string, ExtractExtraInfo> | null>()

enum textType {
    DIR = 0,
    WRI,
    STAR,
    TITLE,
    SUM
}

const onRateEnter = () => {
    rateFixed.value = true
}

const onRateLeave = () => {
    rateFixed.value = false
}

const highlight = (text: string, match: string, type: number) => {
    if (!text || !match) return text

    let stemmedMatches: string[] = []
    const raw = match.split(' ')
    for (let w of raw) {
        if (w.trim() !== '') {
            stemmedMatches.push(w.trim().toLowerCase())
        }
    }

    return text.replace(/\b\w+\b/g, (word) => {
        const stemmedWord = stemmer(word.trim().toLowerCase())
        const rawWord = word.trim().toLocaleLowerCase()
        for (let stemmedMatch of stemmedMatches) {
            if (stemmedWord === stemmedMatch || rawWord === stemmedMatch) {
                return `<span class="highlight">${word}</span>`
            }
        }
        return word
    })
}

const handleSearch = async () => {
    showRate.value = false
    if (!userInput.value.trim()) return

    userInputSave.value = userInput.value

    const loading = ElLoading.service({
        lock: true,
        text: 'Loading',
        background: 'rgba(0, 0, 0, 0.7)',
    })
    const res = await getInfo(userInput.value)
    loading.close()
    // console.log(res)
    if (res.total === 0) {
        ElNotification({
            type: 'error',
            message: 'no content matches'
        })
        return
    }
    showContent.value = true
    showRate.value = true
    searchList.value = res
}

const handleGetExtract = async (doc_id: string) => {
    if (!extractedInfoList.value) {
        extractedInfoList.value = new Map()
    }
    if (extractedInfoList.value.has(doc_id)) {
        extractedInfoList.value.delete(doc_id)
        return
    }
    const res = await getExtractedInfo(doc_id)
    // console.log(res)

    extractedInfoList.value.set(doc_id, res.extracted_info)
}

const handleRate = async (val: number) => {
    userRate.value = val
    const res = await subRate(userInputSave.value, userRate.value)
    if (res.success) {
        ElNotification({
            type: 'success',
            message: res.message
        })
    } else {
        ElNotification({
            type: 'error',
            message: '出错了'
        })
    }
    userRate.value = 0
    showRate.value = false
}

const handleExtractRate = async (val: number, doc_id: string) => {
    extractRate.value?.set(doc_id, val)
    const res = await subExtractRate({
        doc_id,
        evaluation: extractRate.value!.get(doc_id)!
    })
    // console.log(res)
    if (res.success) {
        ElNotification({
            type: 'success',
            message: res.message
        })
    } else {
        ElNotification({
            type: 'error',
            message: '出错了'
        })
    }
    extractRate.value?.set(doc_id, 0)
}
</script>

<template>
    <div class="main">
        <div class="container">
            <div class="search-box">
                <el-input v-model="userInput" style="width: 600px; height: 70px;" placeholder="Type Something..."
                    :prefix-icon="Search" @keyup.enter="handleSearch" />
            </div>
            <transition name="slide-rate" @after-enter="onRateEnter" @before-leave="onRateLeave">
                <div class="rate" :class="{ 'rate-fixed': rateFixed }" v-if="showRate" style="right: 0;">
                    <el-rate v-model="userRate" @change="handleRate" size="large" allow-half />
                </div>
            </transition>

            <div class="search-body">
                <div v-if="searchList.has_corrections" class="correctionsC">
                    <span v-for="(corrected, wrong) in searchList.corrections">
                        "{{ wrong }}"
                    </span>
                    dosen't match any. Results are shown for:
                    <span v-for="(corrected, wrong) in searchList.corrections">
                        "{{ corrected }}"
                    </span>
                </div>
                <ul class="search-list" style="list-style: none;">
                    <li class="search-content" v-for="(item, index) in searchList.results" :key="index">
                        <div class="info"
                            style="display: inline-flex; justify-content: space-between; width: 100%; text-align: center;">
                            <div>
                                Similarity: {{ item.sim }} Target: {{ item.match }}
                            </div>
                            <div>
                                <el-button type="text" @click="handleGetExtract(item.url)">
                                    {{ extractedInfoList?.has(item.url) ? "BACK" : "SHOW EXTRACTED ATTRIBUTES" }}
                                </el-button>
                            </div>
                        </div>
                        <div v-if="extractedInfoList && extractedInfoList.has(item.url)">
                            <div v-if="extractedInfoList.get(item.url)!.keywords.length > 0">
                                <div class="title">Keywords:</div>
                                <ul>
                                    <li v-for="(kItem, index) in extractedInfoList.get(item.url)!.keywords">
                                        <div class="info">{{ kItem }}</div>
                                    </li>
                                </ul>
                            </div>
                            <div v-if="extractedInfoList.get(item.url)!.locations.length > 0">
                                <div class="title">Locations:</div>
                                <ul>
                                    <li v-for="(lItem, index) in extractedInfoList.get(item.url)!.locations">
                                        <div class="info">{{ lItem }}</div>
                                    </li>
                                </ul>
                            </div>
                            <div v-if="extractedInfoList.get(item.url)!.organizations.length > 0">
                                <div class="title">Organizations:</div>
                                <ul>
                                    <li v-for="(oItem, index) in extractedInfoList.get(item.url)!.organizations">
                                        <div class="info">{{ oItem }}</div>
                                    </li>
                                </ul>
                            </div>
                            <div v-if="extractedInfoList.get(item.url)!.persons.length > 0">
                                <div class="title">Persons:</div>
                                <ul>
                                    <li v-for="(pItem, index) in extractedInfoList.get(item.url)!.persons">
                                        <div class="info">{{ pItem }}</div>
                                    </li>
                                </ul>
                            </div>
                            <el-divider></el-divider>
                            <div style="width: 100%; display: inline-flex; justify-content: right;">
                                <el-rate :model-value="extractRate?.get(item.url) ?? 0"
                                    @change="(val: any) => handleExtractRate(val, item.url)" size="large" allow-half />
                            </div>
                        </div>
                        <div v-else>
                            <el-divider></el-divider>
                            <div class="title" v-html="highlight(item.title, item.match, textType.TITLE)"></div>
                            <div class="info">rate: {{ item.rate }}</div>
                            <div class="info">
                                <span>Director: </span>
                                <span class="info" v-html="highlight(item.director, item.match, textType.DIR)"></span>
                            </div>
                            <div class="info">
                                <span>Writers: </span>
                                <span class="info" v-html="highlight(item.writers, item.match, textType.WRI)"></span>
                            </div>
                            <div class="info">
                                <span>Stars: </span>
                                <span class="info" v-html="highlight(item.stars, item.match, textType.STAR)"></span>
                            </div>
                            <div class="summary" v-html="highlight(item.summary, item.match, textType.SUM)"></div>
                            <el-divider></el-divider>
                            <div class="info">
                                <span>Original Website: </span>
                                <a :href="item.url">{{ item.url }}</a>
                            </div>
                            <div class="info">Search Timestamp: {{ searchList.timestamp }}</div>
                            <div class="info">Count: {{ index + 1 }} / {{ searchList.total }} </div>
                        </div>
                    </li>
                </ul>
            </div>
        </div>
    </div>
</template>

<style lang="scss" scoped>
.main {
    min-height: 100vh;
    background-image: linear-gradient(120deg, #e0c3fc 0%, #8ec5fc 100%);
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;

    .rate {
        z-index: 100;
        bottom: 30px;
        height: 50px;
        padding: 9px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        position: fixed;
        box-shadow: 0px 3px 7px rgb(113, 113, 113);
        background-image: linear-gradient(120deg, #f093fb 0%, #f5576c 100%);
        border-radius: 20px;
    }

    .rate-fixed {
        right: 20px !important;
    }

    .container {
        padding: 30px;

        .search-box {
            text-align: center;
            margin-bottom: 30px;
        }

        .search-body {
            padding: 0 40px 0 40px;

            .search-content {
                padding: 30px;
                margin-bottom: 20px;
                border-radius: 20px;
                color: #606266;
                background-color: rgb(255, 255, 255);
                box-shadow: 0px 3px 10px rgb(149, 149, 149);

                .info {
                    font-size: 14px;

                    a {
                        color: #cc89ba;
                    }
                }

                .title {
                    font-weight: bolder;
                    margin-bottom: 10px;
                }

                .summary {
                    margin-top: 10px;
                    font-size: small;
                }
            }
        }
    }
}

.correctionsC {
    font-size: 18px;
    padding-left: 40px;
    padding-right: 40px;
    color: #fff;
}

.slide-rate-enter-active,
.slide-rate-leave-active {
    transition: all 0.5s cubic-bezier(0.4, 0, 0.2, 1);
}

.slide-rate-enter-from,
.slide-rate-leave-to {
    transform: translateX(100%);
}

.slide-rate-enter-to {
    transform: translateX(-20px);
}

::v-deep .highlight {
    background-color: rgb(255, 209, 238);
    font-weight: bold;
}

::v-deep .el-input__wrapper {
    border-radius: 33px;
    box-shadow: 0px 3px 10px rgb(149, 149, 149);

    .el-input__prefix {
        font-size: 18px;
    }

    .el-input__inner {
        font-size: 18px;
    }
}
</style>