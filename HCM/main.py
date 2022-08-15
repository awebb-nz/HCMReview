from Hand_made_generative import *
from Generative_Model import *
import pandas as pd
from train import *
from nn_model import *
from dataset import *
from CG1 import *
import PIL as PIL
from PIL import Image
import os
from chunks import *
import pickle
from PARSER import *


def convergence_hierarchy():
    """Experiment on how learning convergence with increasing hierarchy depth"""

    df = {}

    df["N"] = []
    df["kl"] = []
    df["type"] = []
    df["d"] = []
    df["seql"] = []
    n_sample = 5  # number of samples used for a particular uncommital generative model
    n_atomic = 5
    ds = [3, 5, 7, 8]  # depth of the generative model
    Ns = np.arange(200, 3000, 200)
    for d in ds:  # varying depth, and the corresponding generative model it makes
        depth = d
        for i in range(0, n_sample):
            # in every new sample, a generative model is proposed.
            cg_gt = generative_model_random_combination(D=depth, n=n_atomic)
            cg_gt = to_chunking_graph(cg_gt)
            for n in Ns:
                print({" d ": d, " i ": i, " n ": n})
                # cg_gt = hierarchy1d() #one dimensional chunks
                seq = generate_random_hierarchical_sequence(cg_gt.M, s_length=n)
                cg = Chunking_Graph(
                    DT=0, theta=1
                )  # initialize chunking part with specified parameters
                cg = rational_chunking_all_info(seq, cg)
                imagined_seq = cg.imagination(
                    n, sequential=True, spatial=False, spatial_temporal=False
                )
                kl = evaluate_KL_compared_to_ground_truth(
                    imagined_seq, cg_gt.M, Chunking_Graph(DT=0, theta=1)
                )
                df["N"].append(n)
                df["d"].append(depth)
                df["kl"].append(kl)
                df["type"].append("ck")
                df["seql"].append(0)  # not applicable

                speech = list((seq.flatten().astype("int")))
                speech = "".join(str(e) for e in speech)
                learned_ps, _ = PARSER(
                    speech, PS=dict(zip(np.arange(0, n_atomic, 1), [0] * n_atomic))
                )
                imagined_seq = parser_imagination(learned_ps, n)
                kl_parser = evaluate_KL_compared_to_ground_truth(
                    imagined_seq, cg_gt.M, Chunking_Graph(DT=0, theta=1)
                )
                df["N"].append(n)
                df["d"].append(depth)
                df["kl"].append(kl_parser)
                df["type"].append("parser")
                df["seql"].append(0)  # not applicable

                for seql in [50]:
                    imagined_seq, p = NN_testing(
                        seq, seql=seql
                    )  # comparison with an RNN
                    imagined_seq = np.array(imagined_seq).reshape(
                        [len(imagined_seq), 1, 1]
                    )
                    klnn = evaluate_KL_compared_to_ground_truth(
                        imagined_seq, cg_gt.M, Chunking_Graph(DT=0, theta=1)
                    )
                    df["N"].append(n)
                    df["d"].append(depth)
                    df["kl"].append(klnn)
                    df["type"].append("nn")
                    df["seql"].append(seql)

    df = pd.DataFrame.from_dict(df)
    df.to_pickle(
        "../OutputData/KL_rational_learning_N"
    )  # where to save it, usually as a .pkl
    return df


def NN_testing(sequence, seql=3):
    """Train an RNN to learn sequence and generated imagination based on the learned representations by RNN"""
    # convert the sequence into lists
    # Ns = np.arange(50, 3000, 50)# the length of sequence decided to show neural networks
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-epochs", type=int, default=1)
    parser.add_argument("--batch-size", type=int, default=5)
    parser.add_argument("--sequence-length", type=int, default=seql)
    parser.add_argument("--learning-rate", type=float, default=0.1)

    args = parser.parse_args()

    dataset = Dataset(sequence, args)
    model = Model(dataset)

    train(dataset, model, args)
    imaginary_sequence = predict(dataset, model)
    return imaginary_sequence


def c3_RNN():
    """Compare neural network behavior with human on chunk prediction"""
    sequence = np.array(generateseq("c3", seql=800)).reshape((800, 1, 1))
    sequence[0, :, :] = 0
    # sequence = np.array(generateseq('c3', seql=600)).reshape((600, 1, 1))
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-epochs", type=int, default=1)
    parser.add_argument("--batch-size", type=int, default=5)
    parser.add_argument("--sequence-length", type=int, default=3)
    parser.add_argument("--learning-rate", type=float, default=0.001)
    args = parser.parse_args()
    predicted_seq = []  # list(sequence[0:start].flatten())
    prob = []  # [0.25]*start
    ID = []
    learning_rate = []
    model_type = []
    n_sample = 50
    for lr in [0.001]:
        args.learning_rate = lr
        for s in range(0, n_sample):  # across 30 runs
            for idx in range(200, 800):
                pre_l = 20
                dataset = Dataset(
                    sequence[0 : idx - 1], args
                )  # use all of the past dataset to train
                model = Model(dataset)
                train(dataset, model, args)  # train another model from scratch.
                p_next = evaluate_next_word_probability(
                    model,
                    sequence[idx],
                    words=list(sequence[max(idx - pre_l, 0) : idx, :, :].flatten()),
                )
                predicted_seq.append(sequence[idx])
                prob.append(p_next)
                ID.append(s)
                learning_rate.append(lr)
                model_type.append("model0")

                model1 = Model1(dataset)
                train(dataset, model1, args)  # train another model from scratch.
                p_next = evaluate_next_word_probability(
                    model1,
                    sequence[idx],
                    words=list(sequence[max(idx - pre_l, 0) : idx, :, :].flatten()),
                )
                predicted_seq.append(sequence[idx])
                prob.append(p_next)
                ID.append(s)
                learning_rate.append(lr)
                model_type.append("model1")

                model2 = Model2(dataset)
                train(dataset, model2, args)  # train another model from scratch.
                p_next = evaluate_next_word_probability(
                    model2,
                    sequence[idx],
                    words=list(sequence[max(idx - pre_l, 0) : idx, :, :].flatten()),
                )
                predicted_seq.append(sequence[idx])
                prob.append(p_next)
                ID.append(s)
                learning_rate.append(lr)
                model_type.append("model2")

    df = {}
    df["seq"] = predicted_seq
    df["prob"] = prob
    df["id"] = ID
    df["learning_rate"] = learning_rate
    df["model_type"] = model_type

    import pickle

    with open("../OutputData/c3_RNN.pkl", "wb") as f:
        pickle.dump(df, f)
    return


def p_RNN(trainingseq, MODEL=Model):
    """Train neural network on SRT instruction sequences
    Returns:
        prob (list): prediction probability of the instruction
    """
    sequence = np.array(trainingseq).reshape((-1, 1, 1))
    sequence[0:5, :, :] = np.array([0, 1, 2, 3, 4]).reshape((5, 1, 1))
    # sequence = np.array(generateseq('c3', seql=600)).reshape((600, 1, 1))
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-epochs", type=int, default=1)
    parser.add_argument("--batch-size", type=int, default=5)
    parser.add_argument("--sequence-length", type=int, default=3)
    parser.add_argument("--learning-rate", type=float, default=0.001)

    args = parser.parse_args()
    start = 10
    prob = [0.25] * start
    for idx in range(start, len(trainingseq)):
        dataset = Dataset(
            sequence[:idx, :, :], args
        )  # use all of the past dataset to train
        model = MODEL(dataset)
        train(dataset, model, args)  # train another model from scratch.
        pre_l = 10
        p_next = evaluate_next_word_probability(
            model,
            sequence[idx],
            words=list(sequence[max(idx - pre_l, 0) : idx, :, :].flatten()),
        )
        prob.append(p_next[0][0])
    return prob


def readGif(filename, asNumpy=True):
    # Check PIL
    if PIL is None:
        raise RuntimeError("Need PIL to read animated gif files.")

    # Check Numpy
    if np is None:
        raise RuntimeError("Need Numpy to read animated gif files.")

    # Check whether it exists
    if not os.path.isfile(filename):
        raise IOError("File not found: " + str(filename))

    # Load file using PIL
    pilIm = PIL.Image.open(filename)
    pilIm.seek(0)

    # Read all images inside
    images = []
    try:
        while True:
            # Get image as numpy array
            tmp = pilIm.convert()  # Make without palette
            a = np.asarray(tmp)
            if len(a.shape) == 0:
                raise MemoryError("Too little memory to convert PIL image to array")
            # Store, and next
            images.append(a)
            pilIm.seek(pilIm.tell() + 1)
    except EOFError:
        pass

    # Convert to normal PIL images if needed
    if not asNumpy:
        images2 = images
        images = []
        for im in images2:
            images.append(PIL.Image.fromarray(im))

    # Done
    return images


def squidgifmoving():
    """Experiment on semi-realistic stimuli learning chunks from moving gif sequences"""
    gifarray = readGif("./gif_data/octo_25.gif")  # loads gifs into a list of np arrays
    T = len(
        gifarray
    )  # find a unique combination of colors, assign them as interger, the blue color should be 0
    colormap = []
    cm = 0
    animseq = np.zeros((T, 25, 25))
    for t in range(0, T):
        thisarray = gifarray[t]
        for i in range(0, 25):
            for j in range(0, 25):
                if tuple(thisarray[i, j, :]) not in colormap:
                    colormap.append(tuple(thisarray[i, j, :]))
                    cm = cm + 1
                animseq[t, i, j] = colormap.index(tuple(thisarray[i, j, :]))

    R = 100  # the number of repetition
    totalseq = np.zeros((T * R, 25, 25))
    # make the sequence repeat
    for i in range(0, R):
        totalseq[i * T : (i + 1) * T, :, :] = animseq
    totalseq = totalseq.astype(int)
    # cg = Chunking_Graph(DT=0.1, theta=0.98)  # initialize chunking part with specified parameters
    # cg = learn_stc_classes(totalseq, cg)
    cg = CG1(
        DT=0.01, theta=0.996, pad=1
    )  # initialize chunking part with specified parameters
    cg, chunkrecord = hcm_learning(
        totalseq, cg
    )  # with the rational chunk models, rational_chunk_all_info(seq, cg)
    cg.convert_chunks_in_arrays()
    print(totalseq.shape)
    # transform each chunk into gif array
    # K = sorted(cg.chunks, key=lambda x: x.volume, reverse=True)  # for decreasing order
    # K = sorted(cg.M.items(), key=lambda x: np.sum(tuple_to_arr(x[1])>0), reverse=True)  # for decreasing order
    for k in range(0, len(cg.chunks)):
        # test_chunk = K[k].arraycontent
        test_chunk = cg.chunks[k].arraycontent
        for p in range(0, test_chunk.shape[0]):
            gif_chunk = np.zeros((25, 25, 4))
            for i in range(0, 25):
                for j in range(0, 25):
                    gif_chunk[i, j, :] = np.array(colormap[int(test_chunk[p, i, j])])

            gif_chunk = (
                255.0 / gif_chunk.max() * (gif_chunk - gif_chunk.min())
            ).astype(np.uint8)
            im = Image.fromarray(gif_chunk)
            name = "../OutputData/gifsquid/" + str(k) + "|-" + str(p) + ".png"
            im.save(name)

    return


def fmri():
    """Experiment on learning hierarchies of chunks from fMRI data"""
    import numpy as np

    with open("../InputData/fmri_timeseries/timeseries.npy", "rb") as f:
        whole_time_series = np.load(f)
    subject_learned_chunk = []
    for i in range(0, whole_time_series.shape[0]):
        time_series = whole_time_series[i, :, :]
        seq = time_series.astype(int).reshape(time_series.shape + (1,))
        cg = CG1(
            DT=0.1, theta=1.0, pad=25
        )  # initialize chunking part with specified parameters
        cg, chunkrecord = hcm_learning(
            seq, cg
        )  # with the rational chunk models, rational_chunk_all_info(seq, cg)
        cg.save_graph(name="subject" + str(i), path="./fmri_chunk_data/")
        # reparse the sequence, using the biggest chunks
        cg.reinitialize()
        cg, chunkrecord = hcm_learning(
            seq, cg, learn=False
        )  # with the rational chunk models, rational_chunk_all_info(seq, cg)

        learned_chunk = []  # store chunks learned by cg
        for ck in cg.chunks:
            # record all the chunks
            ck.to_array()
            chunk_array = ck.arraycontent
            freq = ck.count
            learned_chunk.append((chunk_array, freq))
        subject_learned_chunk.append([learned_chunk, chunkrecord])

    with open("../OutputData/fmri_chunk_data/fmri_learned_chunks.npy", "wb") as f:
        np.save(f, subject_learned_chunk)

    return


def rationalfmri():
    """Experiment on running rational chunking model on fMRI data"""
    import numpy as np

    with open("../InputData/fmri_timeseries/timeseries.npy", "rb") as f:
        whole_time_series = np.load(f)
    subject_learned_chunk = []
    for i in range(0, whole_time_series.shape[0]):
        time_series = whole_time_series[i, :, :]
        seq = time_series.astype(int).reshape(time_series.shape + (1,))
        cg = CG1(
            DT=0.1, theta=1.0, pad=40
        )  # initialize chunking part with specified parameters
        cg, chunkrecord = hcm_rational(
            seq, cg
        )  # with the rational chunk models, rational_chunk_all_info(seq, cg)
        cg.save_graph(
            name="subject" + str(i), path="../OutputData/exp/fmri_chunk_data/"
        )

        # store chunks learned by cg
        learned_chunk = []
        for ck in cg.chunks:
            # record all the chunks
            ck.to_array()
            chunk_array = ck.arraycontent
            freq = ck.count
            learned_chunk.append((chunk_array, freq))
        subject_learned_chunk.append([learned_chunk, chunkrecord])

        with open(
            "../OutputData/exp/fmri_chunk_data/fmri_learned_chunks.npy", "wb"
        ) as f:
            np.save(f, subject_learned_chunk)

    return


def visual_chunks():
    """Experiment on compositional visual stimuli with embedded hierarchy"""
    cg_gt = compositional_imgs()
    n = 2000
    seq = generate_hierarchical_sequence(cg_gt.M, s_length=n)
    cg = CG1(DT=0.01, theta=0.996)
    cg, _ = hcm_learning(seq, cg)
    cg.convert_chunks_in_arrays()
    cg.save_graph(name="visual_chunks")
    return


def c3_chunk_learning():
    """Train HCM on c3 condition of SRT instruction sequences"""

    def get_chunk_list(ck):
        # print(np.array(list(ck.content)))
        T = int(max(np.array(list(ck.content)).reshape([-1, 4])[:, 0]) + 1)
        chunk = np.zeros([T], dtype=int)
        for t, _, _, v in ck.content:
            print(ck.content, chunk.size, T)
            chunk[t] = v
        for item in list(chunk):
            if item == 0:
                print("")
        return list(chunk)

    df = {}
    df["time"] = []
    df["chunksize"] = []
    df["ID"] = []

    hcm_chunk_record = {}

    for ID in range(0, 30):  # across 30 runs
        hcm_chunk_record[ID] = []
        seq = np.array(generateseq("c3", seql=600)).reshape((600, 1, 1))
        cg = CG1(
            DT=0.0, theta=0.90
        )  # initialize chunking part with specified parameters
        cg, chunkrecord = hcm_learning(
            seq, cg
        )  # with the rational chunk models, rational_chunk_all_info(seq, cg)
        for time in list(chunkrecord.keys()):
            df["time"].append(int(time))
            ckidx = chunkrecord[time][0][0]
            df["chunksize"].append(cg.chunks[ckidx].volume)
            df["ID"].append(ID)
            chunk = get_chunk_list(cg.chunks[ckidx])
            hcm_chunk_record[ID].append(chunk)
    with open("../OutputData/HCM_time_chunksize.pkl", "wb") as f:
        pickle.dump(df, f)

    with open("../OutputData/HCM_chunk.pkl", "wb") as f:
        pickle.dump(hcm_chunk_record, f)

    return


def rt_human_hcm_rnn():
    """Simulate reaction time for HCM and RNN on SRT task"""
    import pickle

    data = {}
    data["id"] = []
    data["p_rnn_m"] = []
    data["p_hcm"] = []
    data["p_parser"] = []
    data["seq"] = []
    data["rt"] = []
    dfsubject = pd.read_csv("../InputData/human_data/filtered_exp1.csv")
    print(np.unique(dfsubject[dfsubject["condition"] == 2]["id"]))
    for subj in np.unique(
        dfsubject[dfsubject["condition"] == 2]["id"]
    ):  # iterate over all subjects in c3 chunk condition
        print("subj ", subj)
        subseq = []
        for press in list(dfsubject[dfsubject["id"] == subj]["userpress"]):
            if press == list(dfsubject[dfsubject["id"] == subj]["keyassignment"])[0][2]:
                subseq.append(1)
            if press == list(dfsubject[dfsubject["id"] == subj]["keyassignment"])[0][7]:
                subseq.append(2)
            if (
                press
                == list(dfsubject[dfsubject["id"] == subj]["keyassignment"])[0][12]
            ):
                subseq.append(3)
            if (
                press
                == list(dfsubject[dfsubject["id"] == subj]["keyassignment"])[0][17]
            ):
                subseq.append(4)
        trainingseq = subseq[200:800]
        p_hcm = hcm_c3_probability(trainingseq)
        p_rnn = p_RNN(trainingseq, MODEL=Model)

        p_parser = PARSER_c3_probability(trainingseq)

        data["id"] += [subj] * len(p_hcm)
        data["p_rnn"] += p_rnn
        data["p_hcm"] += p_hcm
        data["p_parser"] += p_parser
        data["seq"] += trainingseq
        data["rt"] += list(dfsubject[dfsubject["id"] == subj]["timecollect"])[200:800]

        with open("../OutputData/hcm_rnn_rt_p.pkl", "wb") as f:
            pickle.dump(data, f)
    return


def hcm_c3_probability(training_seq):
    """Evaluate prediction probability of HCM trained on SRT instruction sequences"""
    time_series = np.array(training_seq).reshape([-1, 1, 1])
    seq = time_series.astype(int)
    cg = CG1(DT=0.1, theta=0.90)  # initialize chunking part with specified parameters
    cg, chunkrecord = hcm_learning(
        seq, cg
    )  # with the rational chunk models, rational_chunk_all_info(seq, cg)
    p = []

    for t in range(0, len(seq)):
        if t in list(chunkrecord.keys()):
            freq = chunkrecord[t][0][1]
            p0.append(freq / t)

        else:  # a within-chunk element
            eps = 0.01
            p.append(1 - 4 * eps)

    return p


def transferinterferenceexperiment():
    def transfer_train_measure_KL(cg_trained, cg_test, training_sequence):
        cg_trained = learn_stc_classes(training_sequence, cg_trained)
        imagined_seq_trained = cg_trained.imagination(
            1000, sequential=True, spatial=False, spatial_temporal=False
        )
        kl = evaluate_KL_compared_to_ground_truth(
            imagined_seq_trained, cg_test.M, Chunking_Graph(DT=0, theta=1)
        )
        return kl

    cg_trained = impose_representation()
    int_env = generate_interfering_env()
    fac_env = generate_facilitative_env()
    df = {}
    df["type"] = []
    df["kl"] = []
    df["N"] = []
    df["env"] = []
    Ns = list(np.arange(50, 1000, 50))
    n_sample = 50
    for s in range(0, n_sample):
        for n in Ns:
            # train on facilitative environment
            fccg_trained = Chunking_Graph(DT=0.01, theta=0.996)
            fccg_trained.M = cg_trained.M.copy()
            fccg_trained.vertex_list = cg_trained.vertex_list.copy()
            fccg_trained.edge_list = cg_trained.edge_list.copy()
            fccg_trained.vertex_location = cg_trained.vertex_location.copy()
            fccg_trained.zero = arr_to_tuple(np.zeros([1, 1, 1]))

            faci_seq = generate_hierarchical_sequence(fac_env.M, s_length=n)

            naive = Chunking_Graph(DT=0.01, theta=0.996)
            klfaci = transfer_train_measure_KL(fccg_trained, fac_env, faci_seq)
            klnaivefaci = transfer_train_measure_KL(naive, fac_env, faci_seq)

            # train on interfering environment
            iccg_trained = Chunking_Graph(DT=0.01, theta=0.996)
            iccg_trained.M = cg_trained.M.copy()
            iccg_trained.vertex_list = cg_trained.vertex_list.copy()
            iccg_trained.edge_list = cg_trained.edge_list.copy()
            iccg_trained.vertex_location = cg_trained.vertex_location.copy()
            iccg_trained.zero = arr_to_tuple(np.zeros([1, 1, 1]))

            inte_seq = generate_hierarchical_sequence(int_env.M, s_length=n)

            naive = Chunking_Graph(DT=0.01, theta=0.996)
            klinte = transfer_train_measure_KL(iccg_trained, int_env, inte_seq)
            klnaiveinte = transfer_train_measure_KL(naive, int_env, inte_seq)
            print("")
            # record data
            df["env"] = df["env"] + ["transfer", "transfer", "interfere", "interfere"]
            df["N"] = df["N"] + [n, n, n, n]
            df["kl"] = df["kl"] + [klfaci, klnaivefaci, klinte, klnaiveinte]
            df["type"] = df["type"] + ["trained", "naive", "trained", "naive"]

    dff = pd.DataFrame.from_dict(df)
    dff.to_csv("../OutputData/TransferExperiment")
    return


def chunk_human_hcm_rnn():
    """Chunking behavior of hcm and rnn on human SRT task"""
    c3_chunk_learning()  # Sequence Learning HCM

    c3_parser_learning()  # learning sequence from PARSER

    c3_RNN()  # Sequence Learning RNN
    return


def test_kl_diagnostic():
    for total_chunks in range(5, 40):
        for atomic in range(5, 20):
            nsim = 0
            print("==============================================================")
            for sl in [1000, 10000, 100000]:
                cggt = generative_model_random_combination(D=total_chunks, n=atomic)
                imagined_seq = cggt.imagination(
                    sl, sequential=True, spatial=False, spatial_temporal=False
                )
                kl = evaluate_KL_compared_to_ground_truth(
                    imagined_seq, cggt.M, Chunking_Graph(DT=0, theta=1)
                )
                print(kl)

    return


def test_cggt_generation_validity():
    for D in range(1, 10):
        for n in range(4, 10):
            cggt = generative_model_random_combination(D=D, n=n)
            print("D = ", D, " n = ", n, " sum =", np.sum(list(cggt.M.values())))
    return


def NN_interpretability():
    activation = np.load(
        "/kyb/rg/swu/Desktop/NN_interpretability/activation.npy", allow_pickle=True
    )
    activation = activation.item()

    whole_time_series = activation["1"][0, :, :, :]
    time_series = np.array(whole_time_series)
    seq = time_series.astype(int).reshape(time_series.shape)
    cg = CG1(
        DT=0.1, theta=1.0, pad=40
    )  # initialize chunking part with specified parameters
    cg, chunkrecord = hcm_rational(
        seq, cg, maxIter=5
    )  # with the rational chunk models, rational_chunk_all_info(seq, cg)
    return


def generate_hierarchy_and_rational_learn():
    cggt = generative_model_random_combination(D=4, n=4)
    cggt = to_chunking_graph(cggt)
    seq = generate_random_hierarchical_sequence(cggt.M, s_length=500)
    cg = Chunking_Graph(
        DT=0.01, theta=1
    )  # initialize chunking part with specified parameters
    cg = learn_stc_classes(
        seq, cg
    )  # with the rational chunk models, rational_chunk_all_info(seq, cg)

    # one dimensional rational chunking
    learned_M, _, _, _ = partition_seq_hastily(seq, list(cggt.M.keys()))
    # cg_gt = hierarchy1d()  # one dimensional chunks
    cg = Chunking_Graph(
        DT=0, theta=1
    )  # initialize chunking part with specified parameters
    cg = rational_chunking_all_info(seq, cg, maxit=5)
    return


def sensitivity_analysis():
    def noise_perturbation(seq, eps=0, n=1):
        for i in range(0, seq.shape[0]):
            if np.random.uniform(0, 1) < eps:
                seq[i, :, :] = np.random.choice(np.arange(0, n))
        return seq

    """Experiment on how learning convergence with increasing hierarchy depth is sensitive on perturbations"""
    df = {}

    df["N"] = []
    df["kl"] = []
    df["type"] = []
    df["d"] = []
    df["eps"] = []
    n_sample = 5  # number of samples used for a particular uncommital generative model
    n_atomic = 5
    ds = [3, 5, 8]  # depth of the generative model
    Ns = np.arange(100, 1000, 100)
    for d in ds:  # varying depth, and the corresponding generative model it makes
        depth = d
        for i in range(0, n_sample):
            # in every new sample, a generative model is proposed.
            cg_gt = generative_model_random_combination(D=depth, n=n_atomic)
            cg_gt = to_chunking_graph(cg_gt)
            for n in Ns:
                for eps in [0, 0.001, 0.01, 0.1]:
                    print({" d ": d, " i ": i, " n ": n})
                    # cg_gt = hierarchy1d() #one dimensional chunks
                    seq = generate_random_hierarchical_sequence(cg_gt.M, s_length=n)
                    seq = noise_perturbation(seq, eps=eps, n=n_atomic)
                    cg = Chunking_Graph(
                        DT=0, theta=1
                    )  # initialize chunking part with specified parameters
                    cg = rational_chunking_all_info(seq, cg)
                    imagined_seq = cg.imagination(
                        n, sequential=True, spatial=False, spatial_temporal=False
                    )
                    kl = evaluate_KL_compared_to_ground_truth(
                        imagined_seq, cg_gt.M, Chunking_Graph(DT=0, theta=1)
                    )
                    df["N"].append(n)
                    df["d"].append(depth)
                    df["kl"].append(kl)
                    df["type"].append("ck")
                    df["eps"].append(eps)

    df = pd.DataFrame.from_dict(df)
    df.to_csv("../OutputData/sensitivity_analysis")
    return


def phase_shift_analysis():

    """Experiment on how learning convergence with increasing hierarchy depth is sensitive on perturbations"""
    df = {}

    df["N"] = []
    df["kl"] = []
    df["type"] = []
    df["d"] = []
    df["phase_shift"] = []
    n_sample = 5  # number of samples used for a particular uncommital generative model
    n_atomic = 5
    ds = [5]  # depth of the generative model
    Ns = np.arange(100, 1000, 100)
    for d in ds:  # varying depth, and the corresponding generative model it makes
        depth = d
        for i in range(0, n_sample):
            # in every new sample, a generative model is proposed.
            cg_gt = generative_model_random_combination(D=depth, n=n_atomic)
            cg_gt = to_chunking_graph(cg_gt)
            for n in Ns:
                for step in range(0, 20):

                    print({" d ": d, " i ": i, " n ": n})
                    # cg_gt = hierarchy1d() #one dimensional chunks
                    seq = generate_random_hierarchical_sequence(cg_gt.M, s_length=n)
                    seq = np.roll(seq, step)

                    cg = Chunking_Graph(
                        DT=0, theta=1
                    )  # initialize chunking part with specified parameters
                    cg = rational_chunking_all_info(seq, cg)
                    imagined_seq = cg.imagination(
                        n, sequential=True, spatial=False, spatial_temporal=False
                    )
                    kl = evaluate_KL_compared_to_ground_truth(
                        imagined_seq, cg_gt.M, Chunking_Graph(DT=0, theta=1)
                    )
                    df["N"].append(n)
                    df["d"].append(depth)
                    df["kl"].append(kl)
                    df["type"].append("hcm")
                    df["phase_shift"].append(step)

    df = pd.DataFrame.from_dict(df)
    df.to_csv("../OutputData/phase_shift_analysis")
    return


def main():
    ################## Generative Model ################
    generate_hierarchy_and_rational_learn()

    ################# Measure KL to produce data for the convergence plot ##############
    convergence_hierarchy()

    ################ Compare human performance with RNN ###############
    chunk_human_hcm_rnn()
    rt_human_hcm_rnn()

    ################ Testing Transfer and Intereference Graph Generation Techniques.
    transferinterferenceexperiment()

    ################## Visual Chunks ################
    visual_chunks()

    ################ Squid moving Gif #########################
    squidgifmoving()

    ################ fMRI data #########################
    fmri()
    ##############################################
    sensitivity_analysis()
    ##############################################
    phase_shift_analysis()

    return


if __name__ == "__main__":
    main()
