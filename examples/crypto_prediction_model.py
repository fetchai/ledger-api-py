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

CONTRACT_TEXT = """

persistent graph_state : Graph;
persistent dataloader_state : DataLoader;
persistent optimiser_state : Optimiser;
persistent historics_state : Tensor;

@init
function setup(owner : Address)

  use graph_state;
  use dataloader_state;
  use optimiser_state;
  use historics_state;

  var owner_balance = State<UInt64>(owner);
  owner_balance.set(1000000u64);
  
  // initial graph construction
  var g = graph_state.get(Graph());
  graphSetup(g);
  graph_state.set(g);
  
  // initial dataloader construction
  var dl = dataloader_state.get(DataLoader("tensor"));
  dataloader_state.set(dl);
  
  // initial optimiser setup
  var optimiser = optimiser_state.get(Optimiser("sgd", g, dl, "Input", "Label", "Error"));
  optimiser_state.set(optimiser);
  
  // intial historics setup
  var tensor_shape = Array<UInt64>(3);
  tensor_shape[0] = 1u64;                 // data points are spot price, so size == 1
  tensor_shape[1] = 2048u64;              // previous 2048 data points
  tensor_shape[2] = 1u64;                 // batch size == 1
  var historics = historics_state.get(Tensor(tensor_shape));
  historics_state.set(historics);
  
endfunction

function graphSetup(g : Graph)

    // set up the computation graph
    
    var conv1D_1_filters        = 16;
    var conv1D_1_input_channels = 1;
    var conv1D_1_kernel_size    = 377;
    var conv1D_1_stride         = 3;
    
    var keep_prob_1 = 0.5fp64;
    
    var conv1D_2_filters        = 8;
    var conv1D_2_input_channels = conv1D_1_filters;
    var conv1D_2_kernel_size    = 48;
    var conv1D_2_stride         = 2;
    
    g.addPlaceholder("Input");
    g.addPlaceholder("Label");
    g.addConv1D("hidden_conv1D_1", "Input", conv1D_1_filters, conv1D_1_input_channels,
                    conv1D_1_kernel_size, conv1D_1_stride);
    g.addRelu("relu_1", "hidden_conv1D_1");
    g.addDropout("dropout_1", "relu_1", keep_prob_1);
    g.addConv1D("Output", "dropout_1", conv1D_2_filters, conv1D_2_input_channels,
                            conv1D_2_kernel_size, conv1D_2_stride);
    g.addMeanSquareErrorLoss("Error", "Output", "Label");

endfunction

@action
function setHistorics(new_historics : Tensor)
    use historics_state;
    
    // var historics = historics_state.get();
    historics_state.set(new_historics);
endfunction

@action
function setRandomHistorics()
    use historics_state;
    
    // in this example we don't use setHistorics because we have no source for the data
    // therefore we set random data to demonstrate the process
    var historics = historics_state.get();
    historics.fillRandom();
    historics_state.set(historics);
endfunction

@action
function makePrediction() : Tensor
    use graph_state;
    use historics_state;
    
    var g = graph_state.get();
    var historics = historics_state.get();

    g.setInput("Input", historics);
    var prediction = g.evaluate("Output");

    return prediction;

endfunction

@action
function train(train_data: Tensor, train_labels: Tensor)

    use graph_state;
    use dataloader_state;
    use optimiser_state;
    
    // retrieve the latest graph
    var g = graph_state.get();
 
    // retrieve dataloader and set up the training data and labels
    var dataloader = dataloader_state.get();
    dataloader.addData(train_data, train_labels);
     
    // retrieve the optimiser
    var optimiser = optimiser_state.get();
    optimiser.setGraph(g);
    optimiser.setDataloader(dataloader);
 
    var training_iterations = 1;
    var batch_size = 8u64;
    for(i in 0:training_iterations)
        var loss = optimiser.run(batch_size);
    endfor
endfunction


"""

def main():

    # create our first private key pair
    entity1 = Entity()

    # build the ledger API
    api = LedgerApi('127.0.0.1', 8100)

    # create wealth so that we have the funds to be able to create contracts on the network
    api.sync(api.tokens.wealth(entity1, 1000000000000000))

    # create the smart contract
    contract = SmartContract(CONTRACT_TEXT)

    # deploy the contract to the network
    api.sync(api.contracts.create(entity1, contract, 1000000000))

    # set random historics
    fet_tx_fee = 100000
    api.sync(contract.action(api, 'setRandomHistorics', fet_tx_fee, [entity1]))

    # make a prediction
    fet_tx_fee = 1000000000
    api.sync(contract.action(api, 'makePrediction', fet_tx_fee, [entity1]))

if __name__ == '__main__':
    main()
