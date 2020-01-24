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
import base64

from fetchai.ledger.api import LedgerApi
from fetchai.ledger.contract import Contract
from fetchai.ledger.crypto import Entity

GRAPH_FILE_NAME = "/Users/khan/fetch/models/crypto_price_prediction/bitcoin_price_prediction_graph.bin"

EXAMPLE_INPUT_HISTORICS = "430.573, 428.26, 428.26, 428.26, 428.26, 428.26, 428.26, 428.26, 428.26, 428.26, 428.26, 428.26, 428.26, 428.26, 430.804, 430.804, 430.804, 430.804, 430.804, 430.804, 430.804, 430.804, 430.804, 430.804, 430.804, 430.804, 430.804, 430.804, 430.804, 430.804, 430.804, 431.76, 431.76, 431.76, 431.76, 431.76, 431.76, 431.76, 431.76, 431.76, 431.76, 431.76, 431.76, 431.76, 431.76, 431.76, 431.76, 431.76, 431.76, 431.76, 431.76, 431.76, 431.76, 431.76, 431.76, 431.76, 431.76, 431.76, 431.76, 431.76, 431.76, 431.76, 431.76, 431.76, 431.76, 431.76, 431.76, 431.76, 431.76, 433.01, 433.01, 433.01, 433.01, 432.14, 432.14, 432.14, 432.14, 433.01, 433.01, 433.01, 433.01, 433.01, 433.01, 433.01, 433.01, 433.01, 433.01, 433.01, 433.01, 433.01, 433.01, 433.01, 433.01, 433.01, 433.01, 433.01, 433.01, 433.01, 433.01, 433.01, 433.01, 433.01, 433.01, 433.01, 433.01, 433.01, 433.01, 433.01, 433.01, 433.01, 430.9, 430.9, 430.9, 430.9, 430.9, 430.9, 430.9, 430.9, 430.9, 430.9, 431.76, 431.76, 431.76, 431.76, 431.76, 431.76, 431.76, 431.76, 431.76, 431.76, 431.76, 431.76, 431.76, 432.62, 432.62, 432.62, 432.62, 432.62, 432.62, 432.62, 432.62, 432.62, 432.62, 432.62, 432.62, 432.62, 432.62, 431.76, 431.76, 431.76, 431.76, 431.76, 431.76, 431.76, 431.76, 431.76, 432.62, 432.62, 432.62, 432.62, 432.62, 432.62, 432.62, 432.62, 432.62, 431.76, 431.76, 431.76, 431.75, 431.75, 431.75, 431.75, 431.75, 431.75, 431.75, 429.12, 429.12, 429.12, 429.12, 429.12, 429.12, 429.12, 429.12, 429.12, 429.12, 429.12, 429.12, 429.12, 429.12, 429.12, 431, 431, 431, 431, 431, 431, 431, 431, 431, 432.62, 432.62, 432.62, 432.62, 432.62, 432.62, 432.62, 432.62, 432.62, 428.27, 428.27, 428.27, 428.27, 428.27, 428.27, 428.27, 428.27, 428.27, 428.27, 428.27, 434.07, 434.07, 428.5, 434.07, 434.07, 434.07, 434.07, 434.07, 434.07, 434.07, 434.07, 434.07, 434.07, 434.07, 434.07, 428.6, 428.6, 428.6, 428.6, 428.6, 428.6, 428.6, 432.07, 432.07, 432.07, 432.07, 432.07, 432.07, 432.07, 432.07, 432.07, 432.07, 432.07, 432.07, 432.07, 432.07, 432.07"

CONTRACT_TEXT = """

persistent graph_state : Graph;
persistent dataloader_state : DataLoader;
persistent optimiser_state : Optimiser;
persistent historics_state : Tensor;
persistent prediction_state : Tensor;

// Smart contract initialisation sets up our graph, dataloader, and optimiser
// in this example we hard-code some values such as the expected input data size
// we could, however, easily add new methods that overwrite these values and 
// update the dataloader/optimiser as necessary
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
  tensor_shape[1] = 256u64;              // previous 256 data points
  tensor_shape[2] = 1u64;                 // batch size == 1
  var historics = historics_state.get(Tensor(tensor_shape));
  historics_state.set(historics);
  
endfunction

// Method initial graph setup (we could forgo adding ops/layers
// if the graph would later be set via a call to updateGraph)
function graphSetup(g : Graph)
    // set up a trivial graph
    g.addPlaceholder("Input");
    g.addPlaceholder("Label");
    g.addRelu("Output", "Input");
    g.addMeanSquareErrorLoss("Error", "Output", "Label");
endfunction

// Method to set new historics as data changes
@action
function setHistorics(new_historics: String)
    use graph_state;
    use historics_state;
    use prediction_state;

    // set new historics
    var historics = historics_state.get();
    historics.fromString(new_historics);

    // make new prediction
    var g = graph_state.get();
    g.setInput("Input", historics);
    var prediction = g.evaluate("Output");
    var squeezed_pred = prediction.squeeze();

    // set new historics and graph states
    historics_state.set(historics);
    graph_state.set(g);
    prediction_state.set(squeezed_pred);
endfunction

// method for querying currently set historics
@query
function getHistorics() : String
    use historics_state;
    var historics = historics_state.get();
    var squeezed_historics = historics.squeeze();
    return squeezed_historics.toString();
endfunction

// Method to make a single prediction based on currently set historics
@query
function makePrediction() : String
    use prediction_state;
    var pred = prediction_state.get();
    return pred.toString();
endfunction

// Method for overwriting the current graph
// this can be used either to update the weights
// or to replace with a totally new model
@action
function updateGraph(graph_string : String)
    use graph_state;
    var g = graph_state.get();
    g = g.deserializeFromString(graph_string);
    graph_state.set(g);
endfunction

// method to train the existing graph with current historics data
// labels must be provided
@action
function train(train_labels_string: String)
    use historics_state;
    use graph_state;
    use dataloader_state;
    use optimiser_state;
    
    // retrieve the latest graph
    var g = graph_state.get();
    
    // retrieve the historics
    var historics = historics_state.get();
 
    // retrieve dataloader
    var dataloader = dataloader_state.get();
    
    // add the historics as training data, and add provided labels
    var train_labels : Tensor;
    train_labels.fromString(train_labels_string);
    dataloader.addData(historics, train_labels);
     
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
    entity1 = Entity.from_hex('d5f10ad865fff147ae7fcfdc98b755452a27a345975c8b9b3433ff16f23495fb')

    # build the ledger API
    api = LedgerApi('127.0.0.1', 8100)

    # create the smart contract
    contract = Contract(CONTRACT_TEXT, entity1)

    # deploy the contract to the network
    api.sync(api.contracts.create(entity1, contract, 1000000000))

    # update the graph with a new model
    fet_tx_fee = 100000000
    with open(GRAPH_FILE_NAME, mode='rb') as file:
        print("reading in graph file...")
        rfile = file.read()

        print("encoding to base64 string...")
        b64obj = base64.b64encode(rfile)
        obj = b64obj.decode()

        print("updating smart contract graph...")
        api.sync(contract.action(api, 'updateGraph', fet_tx_fee, [entity1], obj))

    print("finished updating smart contract graph")

    # set one real example input data set
    fet_tx_fee = 100000000
    api.sync(contract.action(api, 'setHistorics', fet_tx_fee, [entity1], EXAMPLE_INPUT_HISTORICS))

    current_historics = contract.query(api, 'getHistorics')
    print("current historics: " + current_historics)

    # make a prediction
    current_prediction = contract.query(api, 'makePrediction')
    print("current prediction: " + current_prediction)


if __name__ == '__main__':
    main()
