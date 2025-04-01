import { llmAxios } from './llm-axios.service.js';

interface LLMResponse {
  message: string;
}

type Method = 'post' | 'get' | 'put';
type Address = `/${string}`;
type CallBack = (err: any, response: LLMResponse | null) => void;
type LLMTask = (
  [Method, Address, LLMRequestData<ChatMetaData>, CallBack]
);

interface MetaData {
  userId: string;
  guildId: string | null;
}
export interface ChatMetaData extends MetaData {
  chat: [string, string][];
}

export interface LLMRequestData<Meta extends MetaData = MetaData> {
  query: string;
  model: string;
  ragType: string;
  namespace: string;
  prompt: string;
  meta: Meta;
}

const QUEUE_INITIAL_SIZE = 10000;


class LLMService {
  protected readonly queue: (undefined | LLMTask)[] = new Array(QUEUE_INITIAL_SIZE);
  protected qIndex: number = 0;
  protected qLength: number = QUEUE_INITIAL_SIZE;
  protected qElements: number = 0;
  
  protected timeout!: ReturnType<typeof setTimeout>;
  
  constructor() {
    this.runQueue();
  }
  
  
  protected async runQueue() {
    try {
      if (this.qElements > 0) {
        const command = this.queue[this.qIndex];
        this.queue[this.qIndex] = undefined;
        --this.qElements;
        ++this.qIndex;
        
        if (command) {
          console.log('Trying to execute command: ', command);
          await this.askLLM(...command);
        }
      }
    } catch (err) {}
    
    this.timeout = setTimeout(() => this.runQueue(), 10);
  }
  
  protected async askLLM(method: Method, address: Address, dataToSend: LLMRequestData<any>, cb: CallBack) {
    const requester = (() => {
      switch (method) {
        case 'post': return llmAxios.post;
        case 'get': return llmAxios.get;
        case 'put': return llmAxios.put;
      }
      
      throw new Error(`LLM_METHOD_UKNOWN:${method}`);
    })();
    
    try {
      const response = await requester(address, dataToSend, {responseType: 'json'});
      
      cb(null, response.data);
    } catch (err) {
      cb(err, null);
    }
  }
  
  async chat(data: any) {
    return this.putToQueue('post', '/query', data);
  }
  
  protected putToQueue(method: 'post', address: '/query',      dataToSend: LLMRequestData<ChatMetaData>): Promise<LLMResponse>;
  protected putToQueue(method: Method, address: `/${string}`, dataToSend: LLMRequestData<any>):          Promise<LLMResponse> {
    return new Promise((resolve, reject) => {
      const returningPromiseCallBack = (err: any, response: LLMResponse | null) => {
        if (err) return reject(err);
        
        return resolve(response as LLMResponse);
      }
      
      this.queue[this.qIndex + this.qElements] = [method, address, dataToSend, returningPromiseCallBack];
      ++this.qElements;
    });
  }
}


export const llmService = new LLMService();
