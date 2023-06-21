from layer.Blockchain import BlockChain


# DAG 平行链结构
class DAG_Consensus:
    def __init__(self, shard_num, ):
        self.shard_num = shard_num
        self.DAG_parallel = [BlockChain(i) for i in range(shard_num)]

if __name__ == '__main__':
    dag = DAG_Consensus(4)
    print(dag.DAG_parallel[0].chain)
