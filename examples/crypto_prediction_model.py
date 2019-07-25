# ------------------------------------------------------------------------------
#
#   Copyright 2018-2019 Fetch.AI Limited
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# ------------------------------------------------------------------------------
from typing import List

from fetchai.ledger.api import LedgerApi
from fetchai.ledger.contract import SmartContract
from fetchai.ledger.crypto import Entity, Address

# TODO - modify BuildModel to be simply load a graphSaveParams
# TODO - calling AddData on dataloader every time we call train might be expensive; we need to add a method for update train data/labels
# TODO - writing dataloader & optimiser to state
# TODO - implement scalar normalisation
#
#

CONTRACT_TEXT = """
@init
function setup(owner : Address)
  var owner_balance = State<UInt64>(owner);
  owner_balance.set(1000000u64);
endfunction

@action
function buildModel(owner : Address)
    // set up the computation graph
    var g = Graph();
    
    var conv1D_1_filters        = 16;
    var conv1D_1_input_channels = 1;
    var conv1D_1_kernel_size    = 377;
    var conv1D_1_stride         = 3;
    
    var keep_prob_1 = 0.5fp64;
    
    var conv1D_2_filters        = 8;
    var conv1D_2_input_channels = conv1D_1_filters;
    var conv1D_2_kernel_size    = 48;
    var conv1D_2_stride         = 2;
    
    graph.addPlaceholder("Input");
    graph.addPlaceholder("Label");
    
    graph.addConv1D("hidden_conv1D_1", "Input", conv1D_1_filters, conv1D_1_input_channels,
                    conv1D_1_kernel_size, conv1D_1_stride);
    graph.addRelu("relu_1", "hidden_conv1D_1");
    
    graph.addDropout("dropout_1", "relu_1", keep_prob_1);
    
    graph.addConv1D("Output", "dropout_1", conv1D_2_filters, conv1D_2_input_channels,
                            conv1D_2_kernel_size, conv1D_2_stride);
    
    graph.addMeanSquareErrorLoss("Error", "Output", "Label");
    
    var graph_state = State<Graph>(owner + "graph");
    graph_state.set(graph);
    
    // set up dataloader
    var  = DataLoader();
    var dataloader_state = State<data_loader>(owner + "data_loader");
    dataloader_state.set(data_loader);
    
    // set up optimiser
    var optimiser = Optimiser("sgd", graph, "Input", "Label", "Error");
    var optimiser_state = State<optimiser>(owner + "optimiser");
    optimiser_state.set(optimiser);

endfunction

@action
function train(owner : Address, train_data: Tensor, train_labels: Tensor)

    // retrieve dataloader and set up the training data and labels
    var data_loader = (State<Dataloader>(owner + "data_loader")).get();
    data_loader.addData("tensor", train_data, train_labels);
    
    // retrieve the optimiser
    var optimiser = (State<Optimiser>(owner + "optimiser")).get();

    var training_iterations = 10;
    var batch_size = 8u64;
    for(i in 0:training_iterations)
        var loss = optimiser.run(data_loader, batch_size);
    endfor
endfunction

@query
function predict(owner : Address, test_data: Tensor)

    // retrieve graph
    var graph = (State<Graph>(owner + "graph")).get();
    
    graph.setInput("Input", test_data);
    return graph.evaluate("Output");

endfunction

"""


def print_address_balances(api: LedgerApi, contract: SmartContract, addresses: List[Address]):
    for idx, address in enumerate(addresses):
        print('Address{}: {:<6d} bFET {:<10d} TOK'.format(idx, api.tokens.balance(address),
                                                          contract.query(api, 'balance', address=address)))
    print()


def main():
    # create our first private key pair
    entity1 = Entity()
    address1 = Address(entity1)

    # # create a second private key pair
    # entity2 = Entity()
    # address2 = Address(entity2)

    # build the ledger API
    api = LedgerApi('127.0.0.1', 8000)

    # create wealth so that we have the funds to be able to create contracts on the network
    api.sync(api.tokens.wealth(entity1, 1000000))

    # create the smart contract
    contract = SmartContract(CONTRACT_TEXT)

    # deploy the contract to the network
    api.sync(api.contracts.create(entity1, contract, 200))

    # # print the current status of all the tokens
    # print('-- BEFORE --')
    # print_address_balances(api, contract, [address1, address2])

    # transfer from one to the other using our newly deployed contract
    # tok_transfer_amount = 200
    fet_tx_fee = 10000
    # api.sync(contract.action(api, 'transfer', fet_tx_fee, [entity1], address1, address2, tok_transfer_amount))
    api.sync(contract.action(api, 'buildModel', fet_tx_fee, [entity1]))

    # print('-- AFTER --')
    # print_address_balances(api, contract, [address1, address2])


if __name__ == '__main__':
    main()
